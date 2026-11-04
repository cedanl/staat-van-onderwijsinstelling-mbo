"""Analyse-object: invoer, tussenlaag, meldingen en de berekende tabellen.

``maak_analyse`` leest de invoer en bouwt de tussenlaag (``peilmomenten``,
``diplomas``, ``Waarneming``). ``bereken`` rekent daarop alle tabellen die de
app en ``smbo staat`` tonen; beide gebruiken dezelfde functies.
"""

from dataclasses import dataclass, field
from pathlib import Path

import polars as pl
from mbo_bekostiging_bestanden.waardenlijsten import (
    leertrajecten_buiten_indicatorpopulatie,
)

import staat_mbo
from staat_mbo import cohorten as coh
from staat_mbo import indicatoren as ind
from staat_mbo import overzicht as ov
from staat_mbo.bron import InvoerFout, laad_star
from staat_mbo.definities import CATEGORIE_TOELICHTING, DEFINITIES
from staat_mbo.duur import (
    MIN_INSCHRIJVINGEN_DUUR,
    duur_per_opleiding,
    nominale_duur,
)
from staat_mbo.historie import Melding, meldingen
from staat_mbo.loopbaan import canoniek, diplomas, opvolgers, peilmomenten
from staat_mbo.stapelcontrole import Stapelrapport, controleer_stapel
from staat_mbo.waarneming import Waarneming, waarneming

## De demodata (nep-RO's van één instelling) die met het pakket meekomt.
DEMODATA = Path(staat_mbo.__file__).parent / "demodata"
_P = "_persoon_id"
_OPLEIDING = ["Opleidingcode", "Niveau", "Leertraject"]
_COHORT = ["Cohort", *_OPLEIDING]
## Loopbaanstatus wordt na 1, 2 en 3 jaar bepaald.
LOOPBAAN_JAREN = (1, 2, 3)


@dataclass
class Analyse:
    """Alles wat de pagina's en de CLI nodig hebben."""

    rapport: Stapelrapport
    waarneming: Waarneming | None = None
    peilmomenten: pl.DataFrame | None = None
    diplomas: pl.DataFrame | None = None
    duur: pl.DataFrame | None = None
    opvolgers: dict[str, str] = field(default_factory=dict)
    opleidingen: pl.DataFrame | None = None
    meldingen: list[Melding] = field(default_factory=list)
    sleutel: str = ""

    @property
    def ok(self) -> bool:
        return self.rapport.ok

    def regels(self) -> list[str]:
        """Meldingen voor de gebruiker: stapelcontrole eerst, dan de historie."""
        return [
            *self.rapport.meldingen(),
            *(
                f"{'Let op' if m.ernst == 'waarschuwing' else 'Info'}: {m.tekst}"
                for m in self.meldingen
            ),
        ]


def _opleidingen(star: dict[str, pl.DataFrame], kaart: dict[str, str]) -> pl.DataFrame:
    """Naam en domein per crebo, ook voor opvolgers die zelf geen rij hebben.

    Een opvolger zonder eigen rij in ``dim_opleiding`` krijgt de naam en het
    domein van zijn voorganger, zodat de pagina's geen kale crebo's tonen.
    """
    dim = (
        star["dim_opleiding"]
        .select(
            pl.col("Opleidingcode").cast(pl.Utf8),
            pl.col("Opleiding_naam").cast(pl.Utf8),
            pl.col("Opleiding_domein").cast(pl.Utf8),
        )
        .unique("Opleidingcode", keep="first", maintain_order=True)
    )
    bekend = set(dim["Opleidingcode"])
    erbij = (
        dim.filter(pl.col("Opleidingcode").is_in(list(kaart)))
        .with_columns(pl.col("Opleidingcode").replace(kaart))
        .filter(~pl.col("Opleidingcode").is_in(list(bekend)))
        .unique("Opleidingcode", keep="last", maintain_order=True)
    )
    return pl.concat([dim, erbij])


def _standaardduur_melding(pm: pl.DataFrame, duur: pl.DataFrame) -> list[Melding]:
    opleidingen = (
        pm.filter(
            pl.col("Niveau").is_not_null()
            & ~pl.col("Leertraject").is_in(leertrajecten_buiten_indicatorpopulatie())
        )
        .select("Opleidingcode", "Leertraject", "Niveau")
        .unique(["Opleidingcode", "Leertraject"])
    )
    if opleidingen.is_empty():
        return []
    zonder = duur_per_opleiding(duur, opleidingen)["Duur_bron"].eq("standaard").sum()
    if not zonder:
        return []
    return [
        Melding(
            "info",
            f"{zonder} van de {opleidingen.height} opleidingen (per leerweg) hebben "
            f"minder dan {MIN_INSCHRIJVINGEN_DUUR} inschrijvingen om de nominale duur "
            "uit de geplande einddatum te halen; daar geldt de standaardduur per "
            "niveau (1, 2, 3 of 4 jaar).",
        )
    ]


def maak_analyse(invoer: list[Path], werkmap: Path) -> Analyse:
    """Lees de invoer en bouw de tussenlaag; fouten komen in ``rapport.fouten``.

    Args:
        invoer:  Ruwe RO/TBG-i-bestanden, een datamodel-map, parquet of zip.
        werkmap: Map voor tussenbestanden.
    """
    try:
        star = laad_star(invoer, werkmap)
        rapport = controleer_stapel(star)
        if not rapport.ok:
            return Analyse(rapport)
        w = waarneming(star)
    except (InvoerFout, ValueError) as e:
        return Analyse(Stapelrapport([], [], [], 0, fouten=[str(e)]))
    pm, dip = peilmomenten(star), diplomas(star)
    duur = nominale_duur(star)
    kaart = opvolgers(star)
    return Analyse(
        rapport=rapport,
        waarneming=w,
        peilmomenten=pm,
        diplomas=dip,
        duur=duur,
        opvolgers=kaart,
        opleidingen=_opleidingen(star, kaart),
        meldingen=[*meldingen(w), *_standaardduur_melding(pm, duur)],
        sleutel=str(
            hash((pm.hash_rows().sum(), dip.hash_rows().sum(), pm.height, dip.height))
        ),
    )


@dataclass
class Resultaten:
    """De berekende tabellen, alleen geaggregeerd (geen studentniveau)."""

    studiesucces: pl.DataFrame
    instroom: pl.DataFrame
    cohorten: pl.DataFrame
    loopbanen: pl.DataFrame
    overgangen: pl.DataFrame


def studiesucces(a: Analyse) -> pl.DataFrame:
    """Driejaarscijfers van JR, DR en SR voor alle groepen, met norm.

    Onder de minimale noemer is ``Percentage`` leeg (en dus ook ``Onder_norm``).
    """
    delen = []
    for naam, functie in (
        ("jr", ind.jaarresultaat),
        ("dr", ind.diplomaresultaat),
        ("sr", ind.startersresultaat),
    ):
        eenjaars = functie(a.peilmomenten, a.diplomas, a.waarneming, a.opvolgers)
        delen += [
            ind.driejaarscijfer(eenjaars, naam, a.waarneming, groep)
            for groep in ind.GROEPEN
        ]
    klein = pl.col("Te_klein")
    return (
        pl.concat(delen, how="vertical_relaxed")
        .with_columns(
            pl.when(~klein).then(pl.col("Percentage")).alias("Percentage"),
            pl.when(~klein).then(pl.col("Onder_norm")).alias("Onder_norm"),
        )
        .sort(["Indicator", "Jaartijdvak", "Groep", *_OPLEIDING], nulls_last=True)
    )


def _uitval_na_duur(c: pl.DataFrame, r: pl.DataFrame, a: Analyse) -> pl.Series:
    """Uitval na de nominale duur van elke cohortrij (null zonder duur)."""
    uit = pl.Series("Uitval_duur", [None] * r.height, dtype=pl.Boolean)
    for d in sorted(r["Duur"].drop_nulls().unique().to_list()):
        u = coh.uitval(c, a.peilmomenten, a.diplomas, a.waarneming, d, a.opvolgers)[
            "Uitval"
        ]
        uit = pl.select(pl.when(r["Duur"] == d).then(u).otherwise(uit)).to_series()
    return uit.alias("Uitval_duur")


def _cohorten(a: Analyse, c: pl.DataFrame) -> pl.DataFrame:
    """Rendement en uitval per cohort × opleiding, met de herkomst van de instroom."""
    r = coh.rendement(c, a.diplomas, a.duur, a.waarneming, a.opvolgers)
    uit1 = coh.uitval(c, a.peilmomenten, a.diplomas, a.waarneming, 1, a.opvolgers)[
        "Uitval"
    ].alias("Uitval_1")
    r = r.with_columns(uit1, _uitval_na_duur(c, r, a))
    extra = r.group_by(_COHORT).agg(
        pl.col("Nominaal").is_not_null().sum().cast(pl.Int64).alias("N_nominaal"),
        pl.col("Nominaal_plus_1")
        .is_not_null()
        .sum()
        .cast(pl.Int64)
        .alias("N_nominaal_plus_1"),
        pl.col("Uitval_1").sum().cast(pl.Int64).alias("Uitval_1_aantal"),
        pl.col("Uitval_1").is_not_null().sum().cast(pl.Int64).alias("N_uitval_1"),
        coh.percentage_waar("Uitval_1").alias("Uitval_1_percentage"),
        pl.col("Uitval_duur").sum().cast(pl.Int64).alias("Uitval_duur_aantal"),
        pl.col("Uitval_duur").is_not_null().sum().cast(pl.Int64).alias("N_uitval_duur"),
        coh.percentage_waar("Uitval_duur").alias("Uitval_duur_percentage"),
    )
    herkomst = (
        c.group_by([*_COHORT, "Herkomst"])
        .len()
        .pivot(on="Herkomst", index=_COHORT, values="len")
        .rename({h: f"Instroom_{h}" for h in coh.HERKOMSTEN}, strict=False)
    )
    for h in coh.HERKOMSTEN:
        if f"Instroom_{h}" not in herkomst.columns:
            herkomst = herkomst.with_columns(
                pl.lit(0, dtype=pl.UInt32).alias(f"Instroom_{h}")
            )
    herkomst = herkomst.with_columns(
        pl.col(f"Instroom_{h}").fill_null(0).cast(pl.Int64) for h in coh.HERKOMSTEN
    ).select([*_COHORT, *(f"Instroom_{h}" for h in coh.HERKOMSTEN)])
    return (
        coh.rendement_per_groep(r)
        .join(extra, on=_COHORT, how="left")
        .join(herkomst, on=_COHORT, how="left")
        .sort(_COHORT)
    )


def _loopbanen(a: Analyse, c: pl.DataFrame) -> pl.DataFrame:
    """Aantal cohortrijen per cohort × opleiding × loopbaanstatus na 1, 2 en 3 jaar."""
    delen = [
        coh.loopbaanstatus(c, a.peilmomenten, a.diplomas, a.waarneming, k, a.opvolgers)
        .group_by([*_COHORT, "Jaren", "Status"])
        .len()
        .rename({"len": "Aantal"})
        for k in LOOPBAAN_JAREN
    ]
    return pl.concat(delen).sort([*_COHORT, "Jaren", "Status"])


def _overgangen(a: Analyse) -> pl.DataFrame:
    """Niveau op 1-10-t naar het niveau op 1-10-(t+1), met en zonder diploma in t."""
    w = a.waarneming
    jaren = [t for t in range(w.eerste_jaar, w.laatste_jaar) if w.reeks(t, t + 1)]
    van = a.peilmomenten.filter(
        pl.col("Niveau").is_between(1, 4)
        & ~pl.col("Leertraject").is_in(leertrajecten_buiten_indicatorpopulatie())
        & pl.col("Jaar").is_in(jaren)
    )
    naar = a.peilmomenten.select(
        _P,
        (pl.col("Jaar") - 1).alias("Jaar"),
        pl.col("Niveau").alias("_naar"),
        pl.lit(True).alias("_aanwezig"),
    )
    diploma = (
        a.diplomas.select(_P, pl.col("Jaartijdvak").alias("Jaar"))
        .unique()
        .with_columns(pl.lit(True).alias("Diploma"))
    )
    return (
        van.join(naar, on=[_P, "Jaar"], how="left")
        .join(diploma, on=[_P, "Jaar"], how="left")
        .with_columns(
            pl.when(pl.col("_aanwezig").is_null())
            .then(pl.lit("weg"))
            .when(pl.col("_naar").is_null())
            .then(pl.lit("onbekend"))
            .otherwise(pl.concat_str(pl.lit("n"), pl.col("_naar")))
            .alias("Naar"),
            pl.col("Diploma").fill_null(False),
        )
        .group_by(["Jaar", *_OPLEIDING, "Naar", "Diploma"])
        .len()
        .rename({"len": "Aantal"})
        .sort(["Jaar", *_OPLEIDING, "Naar", "Diploma"])
    )


def bereken(a: Analyse) -> Resultaten:
    """Alle tabellen van de app en de CLI (``a.ok`` moet waar zijn)."""
    c = coh.instroomcohorten(a.peilmomenten, a.diplomas, a.waarneming, a.opvolgers)
    instroom = (
        canoniek(c, a.opvolgers)
        .group_by([*_COHORT, "Herkomst"])
        .len()
        .rename({"len": "Aantal"})
        .sort([*_COHORT, "Herkomst"])
    )
    if c.is_empty():
        cohorten = pl.DataFrame()
        loopbanen = pl.DataFrame(
            schema={
                "Cohort": pl.Int32,
                "Opleidingcode": pl.Utf8,
                "Niveau": pl.Int32,
                "Leertraject": pl.Utf8,
                "Jaren": pl.Int32,
                "Status": pl.Utf8,
                "Aantal": pl.UInt32,
            }
        )
    else:
        cohorten, loopbanen = _cohorten(a, c), _loopbanen(a, c)
    return Resultaten(
        studiesucces=studiesucces(a),
        instroom=instroom,
        cohorten=cohorten,
        loopbanen=loopbanen,
        overgangen=_overgangen(a),
    )


def dekking(w: Waarneming) -> pl.DataFrame:
    """Per indicator en jaartijdvak: "ja", "onvolledig" of "nee".

    "ja": waarneembaar en volledig. "onvolledig": waarneembaar, maar een
    ondergrens (DR) of met een kortere terugblik dan zes jaar (SR).
    """

    def stand(naam: str, t: int, mogelijk: set[int]) -> str:
        if t not in mogelijk:
            return "nee"
        return "ja" if ind.volledig(naam, w, t) else "onvolledig"

    rijen = []
    for naam in ("jr", "dr", "sr"):
        mogelijk = set(ind.waarneembare_jaren(naam, w))
        rijen.append(
            {
                "Indicator": naam.upper(),
                **{
                    f"{t}-{t + 1}": stand(naam, t, mogelijk)
                    for t in range(w.eerste_jaar, w.laatste_jaar + 1)
                },
            }
        )
    return pl.DataFrame(rijen)


@dataclass(frozen=True)
class Kerncijfer:
    """Eén tegel van de Start-pagina: naam, waarde, ondertitel en helptekst."""

    naam: str
    waarde: str
    ondertitel: str
    help: str | None = None
    getal: float | None = None


def _driejaar(r: Resultaten, indicator: str) -> tuple[float, str] | str:
    """Laatste volledige driejaarscijfer van de instelling, of de reden zonder."""
    d = r.studiesucces.filter(
        (pl.col("Groep") == "instelling") & (pl.col("Indicator") == indicator)
    )
    if d.is_empty():
        return "nog geen driejaarscijfer: te weinig waarneembare jaren"
    volledig = d.filter(pl.col("Volledig") & pl.col("Percentage").is_not_null())
    if volledig.is_empty():
        return "geen volledige periode (onvolledig of te weinig studenten)"
    rij = volledig.sort("Jaartijdvak").row(-1, named=True)
    return rij["Percentage"], rij["Periode"]


def _tegel_driejaar(r: Resultaten, naam: str, sleutel: str) -> Kerncijfer:
    uit = _driejaar(r, sleutel.upper())
    if isinstance(uit, str):
        return Kerncijfer(naam, ov.pct(None), uit, DEFINITIES[sleutel])
    waarde, periode = uit
    return Kerncijfer(
        naam, ov.pct(waarde), f"driejaarscijfer {periode}", DEFINITIES[sleutel], waarde
    )


def _tegel_instroom(r: Resultaten) -> Kerncijfer:
    hulp = DEFINITIES["instroomcohort"]
    instroom = r.instroom.group_by("Cohort").agg(pl.col("Aantal").sum()).sort("Cohort")
    if instroom.is_empty():
        return Kerncijfer("Instroom", "–", "geen instroomcohort", hulp)
    cohort, n = instroom.row(-1)
    return Kerncijfer(
        "Instroom", str(n), f"instroomcohort {cohort}, studenten", hulp, n
    )


def _tegel_uitval(r: Resultaten) -> Kerncijfer:
    naam, hulp = "Uitval na 1 jaar", DEFINITIES["uitval"]
    bekend = (
        ov.rendement_aggregeer(r.cohorten, ["Cohort"])
        .filter((pl.col("N_uitval_1") == pl.col("Instroom")) & (pl.col("Instroom") > 0))
        .sort("Cohort")
        if not r.cohorten.is_empty()
        else r.cohorten
    )
    if bekend.is_empty():
        return Kerncijfer(
            naam, "–", "nog geen cohort waarvan dit na 1 jaar bekend is", hulp
        )
    rij = bekend.row(-1, named=True)
    return Kerncijfer(
        naam,
        ov.pct(rij["Uitval_1_percentage"]),
        f"instroomcohort {rij['Cohort']}",
        hulp,
        rij["Uitval_1_percentage"],
    )


## Na hoeveel jaar we doorstroom meten: de gangbare duur van een mbo-opleiding.
DOORSTROOM_JAREN = 3


def _tegel_doorstroom(r: Resultaten) -> Kerncijfer:
    """Van de instromers met een diploma: aandeel dat verder ging op hoger niveau.

    Gemeten na ``DOORSTROOM_JAREN`` (of korter als dat nog niet kan), voor het
    laatste cohort dat dan helemaal waarneembaar is. Als aandeel van alle
    instromers zou het cijfer vooral laten zien hoeveel er nog studeren.
    """
    naam, verder, onbekend = (
        "Doorstroom na diploma",
        coh.CATEGORIEEN[0],
        coh.CATEGORIEEN[8],
    )
    met_diploma = coh.CATEGORIEEN[:3]
    hulp = f"{DEFINITIES['loopbaanstatus']}\n\n{CATEGORIE_TOELICHTING[verder]}"
    status = pl.col("Status")
    per_cohort = (
        r.loopbanen.filter(pl.col("Jaren") <= DOORSTROOM_JAREN)
        .group_by("Jaren", "Cohort")
        .agg(
            pl.col("Aantal").filter(status.is_in(met_diploma)).sum().alias("dipl"),
            pl.col("Aantal").filter(status == verder).sum().alias("verder"),
            pl.col("Aantal").filter(status == onbekend).sum().alias("nog"),
        )
        .filter((pl.col("nog") == 0) & (pl.col("dipl") > 0))
        .sort("Jaren", "Cohort")
    )
    if per_cohort.is_empty():
        return Kerncijfer(naam, "–", "nog geen cohort met diploma's waarneembaar", hulp)
    rij = per_cohort.row(-1, named=True)
    deel = round(rij["verder"] / rij["dipl"] * 100, 1)
    return Kerncijfer(
        naam,
        ov.pct(deel),
        f"van de gediplomeerden, instroomcohort {rij['Cohort']}, na {rij['Jaren']} jaar",
        hulp,
        deel,
    )


def kerncijfers(r: Resultaten) -> list[Kerncijfer]:
    """De zes kerncijfers op instellingsniveau, uit de bestaande tabellen.

    Jaar-, diploma- en startersresultaat: driejaarscijfer van de laatste volledige
    periode (geen norm). Instroom: laatste instroomcohort. Uitval na 1 jaar: laatste
    cohort waarvan dat voor het hele cohort waarneembaar is. Doorstroom: van de
    gediplomeerden het aandeel "Diploma, verder op hoger niveau", na drie jaar.
    """
    return [
        _tegel_driejaar(r, "Jaarresultaat", "jr"),
        _tegel_driejaar(r, "Diplomaresultaat", "dr"),
        _tegel_driejaar(r, "Startersresultaat", "sr"),
        _tegel_instroom(r),
        _tegel_uitval(r),
        _tegel_doorstroom(r),
    ]
