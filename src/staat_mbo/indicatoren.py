"""Inspectie-indicatoren per jaartijdvak: jaar-, diploma- en startersresultaat.

Alles rekent op de mbo-tussenlaag (``peilmomenten``, ``diplomas``) en de
``Waarneming``; zie ontwerp §5. De uitvoer heeft per opleiding (crebo × niveau ×
leerweg) een teller en een noemer per jaartijdvak.
"""

from datetime import date

import polars as pl
from mbo_bekostiging_bestanden.indicatoren import norm_voor
from mbo_bekostiging_bestanden.waardenlijsten import (
    leertrajecten_buiten_indicatorpopulatie,
)

from staat_mbo.waarneming import Waarneming

_P = "_persoon_id"
## Niveau 1 (entree) valt buiten alle drie de indicatoren (UWEB art. 4a.2, lid 2).
NIVEAUS = [2, 3, 4]
OPLEIDING = ["Opleidingcode", "Niveau", "Leertraject"]
_RESULTAAT = ["Jaartijdvak", *OPLEIDING, "Teller", "Noemer"]


def _populatie() -> pl.Expr:
    """Binnen de indicatorpopulatie: niveau 2-4 en geen OVO/ODT."""
    return pl.col("Niveau").is_in(NIVEAUS) & ~pl.col("Leertraject").is_in(
        leertrajecten_buiten_indicatorpopulatie()
    )


def _som(*delen: pl.DataFrame) -> pl.DataFrame:
    """Tel tellers en noemers per jaartijdvak en opleiding bij elkaar op."""
    return (
        pl.concat(delen)
        .group_by(["Jaartijdvak", *OPLEIDING])
        .agg(pl.col("Teller").sum(), pl.col("Noemer").sum())
        .select(_RESULTAAT)
        .sort(["Jaartijdvak", "Opleidingcode", "Leertraject"])
    )


def _met_teller(df: pl.DataFrame, teller: int, noemer: int = 1) -> pl.DataFrame:
    return df.select(
        pl.col("Jaartijdvak").cast(pl.Int32),
        *OPLEIDING,
        pl.lit(teller, dtype=pl.Int64).alias("Teller"),
        pl.lit(noemer, dtype=pl.Int64).alias("Noemer"),
    )


def _verlaters(pm: pl.DataFrame, jaren: list[int]) -> pl.DataFrame:
    """Personen in P(t) die niet in P(t+1) staan, met hun opleiding in P(t).

    Alleen personen in de indicatorpopulatie; ``Jaartijdvak`` is t. Wie op
    1 oktober bij een eigen BRIN staat, in welke opleiding ook, is geen verlater.
    """
    volgend = pm.select(_P, (pl.col("Jaar") - 1).alias("Jaar")).unique()
    return (
        pm.filter(_populatie() & pl.col("Jaar").is_in(jaren))
        .join(volgend, on=[_P, "Jaar"], how="anti")
        .rename({"Jaar": "Jaartijdvak"})
        .select(_P, "Jaartijdvak", *OPLEIDING)
    )


def _jaren_jr_dr(w: Waarneming) -> list[int]:
    return [t for t in range(w.eerste_jaar, w.laatste_jaar) if w.reeks(t, t + 1)]


def jaarresultaat(pm: pl.DataFrame, dip: pl.DataFrame, w: Waarneming) -> pl.DataFrame:
    """Jaarresultaat per jaartijdvak en opleiding (ontwerp §5.1).

    Teller: gediplomeerden met een diploma 2-4 in het jaartijdvak, toegerekend
    aan het laatste diploma, ook als ze pas na 1 oktober instroomden. Noemer:
    die gediplomeerden plus de ongediplomeerde instellingsverlaters. Wie
    zonder diploma blijft, telt niet mee.
    """
    jaren = _jaren_jr_dr(w)
    laatste = (
        dip.filter(pl.col("Niveau").is_in(NIVEAUS) & pl.col("Jaartijdvak").is_in(jaren))
        .sort(
            [_P, "Jaartijdvak", "Datum", "Niveau", "Opleidingcode"],
            descending=[False, False, True, True, False],
        )
        .unique([_P, "Jaartijdvak"], keep="first", maintain_order=True)
    )
    gediplomeerd = laatste.select(_P, "Jaartijdvak")
    ongediplomeerd = _verlaters(pm, jaren).join(
        gediplomeerd, on=[_P, "Jaartijdvak"], how="anti"
    )
    return _som(
        _met_teller(laatste.filter(_populatie()), teller=1),
        _met_teller(ongediplomeerd, teller=0),
    )


## Een diploma telt voor het diplomaresultaat mee tot vijf jaar vóór het jaartijdvak.
DIPLOMA_JAREN_TERUG = 5


def dr_volledig(w: Waarneming, t: int) -> bool:
    """Zitten alle diploma's van 1-10-(t-5) af in de bestanden?"""
    return w.diplomas_vanaf <= date(t - DIPLOMA_JAREN_TERUG, 10, 1)


def diplomaresultaat(
    pm: pl.DataFrame, dip: pl.DataFrame, w: Waarneming
) -> pl.DataFrame:
    """Diplomaresultaat per jaartijdvak en opleiding (ontwerp §5.2).

    Noemer: instellingsverlaters, toegerekend aan de opleiding waaruit ze
    vertrekken. Teller: verlaters met een diploma 2-4 uit het jaartijdvak of de
    vijf jaar ervoor, van welk crebo of niveau ook (een stapelaar die uitvalt
    telt positief). ``Volledig``: de diplomahistorie reikt ver genoeg terug.
    """
    jaren = _jaren_jr_dr(w)
    verlaters = _verlaters(pm, jaren)
    vanaf = pl.date(pl.col("Jaartijdvak") - DIPLOMA_JAREN_TERUG, 10, 1)
    tot = pl.date(pl.col("Jaartijdvak") + 1, 9, 30)
    met_diploma = (
        verlaters.select(_P, "Jaartijdvak")
        .join(dip.filter(pl.col("Niveau").is_in(NIVEAUS)), on=_P)
        .filter(pl.col("Datum").is_between(vanaf, tot))
        .select(_P, "Jaartijdvak")
        .unique()
        .with_columns(pl.lit(1, dtype=pl.Int64).alias("Teller"))
    )
    uit = (
        verlaters.join(met_diploma, on=[_P, "Jaartijdvak"], how="left")
        .with_columns(
            pl.col("Teller").fill_null(0), pl.lit(1, dtype=pl.Int64).alias("Noemer")
        )
        .select(_RESULTAAT)
    )
    volledig = {t: dr_volledig(w, t) for t in jaren}
    return _som(uit).with_columns(
        pl.col("Jaartijdvak")
        .replace_strict(volledig, return_dtype=pl.Boolean)
        .alias("Volledig")
    )


## Het startersresultaat kijkt hooguit zes 1 oktobers terug (regeling art. 3, lid 2).
STARTERS_JAREN_TERUG = 6


def sr_terugblik(w: Waarneming, t: int) -> int:
    """Hoeveel 1 oktobers vóór t we mogen bekijken (0 = geen terugblik mogelijk)."""
    return max(0, min(STARTERS_JAREN_TERUG, t - w.eerste_jaar))


def _jaren_sr(w: Waarneming) -> list[int]:
    return [
        t
        for t in range(w.eerste_jaar + 1, w.laatste_jaar)
        if w.reeks(t - sr_terugblik(w, t), t + 1)
    ]


def startersresultaat(
    pm: pl.DataFrame, dip: pl.DataFrame, w: Waarneming
) -> pl.DataFrame:
    """Startersresultaat per jaartijdvak en opleiding (ontwerp §5.3).

    Nieuw: op 1-10-t ingeschreven en op geen van de voorgaande (hooguit zes)
    waarneembare 1 oktobers. Positief: een diploma 2-4 in het jaartijdvak, of
    op 1-10-(t+1) nog ingeschreven op niveau 2-4 (opstromen en wisselen blijven
    positief, afstromen naar entree niet). ``Terugblik`` is het aantal
    bekeken jaren; onder de 6 is het cijfer niet volledig.
    """
    jaren = _jaren_sr(w)
    terugblik = {t: sr_terugblik(w, t) for t in jaren}
    kandidaat = pm.filter(_populatie() & pl.col("Jaar").is_in(jaren)).with_columns(
        pl.col("Jaar")
        .replace_strict(terugblik, return_dtype=pl.Int32, default=0)
        .alias("_k")
    )
    eerder = pl.concat(
        [
            pm.select(
                _P,
                (pl.col("Jaar") + d).alias("Jaar"),
                pl.lit(d, dtype=pl.Int32).alias("_d"),
            )
            for d in range(1, STARTERS_JAREN_TERUG + 1)
        ]
    )
    bekend = (
        kandidaat.join(eerder, on=[_P, "Jaar"])
        .filter(pl.col("_d") <= pl.col("_k"))
        .select(_P, "Jaar")
        .unique()
    )
    nieuw = kandidaat.join(bekend, on=[_P, "Jaar"], how="anti").rename(
        {"Jaar": "Jaartijdvak"}
    )
    diploma = (
        dip.filter(pl.col("Niveau").is_in(NIVEAUS))
        .select(_P, "Jaartijdvak")
        .unique()
        .with_columns(pl.lit(True).alias("_diploma"))
    )
    volgend = (
        pm.filter(pl.col("Niveau").is_in(NIVEAUS))
        .select(_P, (pl.col("Jaar") - 1).alias("Jaartijdvak"))
        .unique()
        .with_columns(pl.lit(True).alias("_blijft"))
    )
    uit = (
        nieuw.join(diploma, on=[_P, "Jaartijdvak"], how="left")
        .join(volgend, on=[_P, "Jaartijdvak"], how="left")
        .select(
            "Jaartijdvak",
            *OPLEIDING,
            (pl.col("_diploma") | pl.col("_blijft"))
            .fill_null(False)
            .cast(pl.Int64)
            .alias("Teller"),
            pl.lit(1, dtype=pl.Int64).alias("Noemer"),
            pl.col("_k").alias("Terugblik"),
        )
    )
    return (
        uit.group_by(["Jaartijdvak", *OPLEIDING, "Terugblik"])
        .agg(pl.col("Teller").sum(), pl.col("Noemer").sum())
        .select([*_RESULTAAT, "Terugblik"])
        .sort(["Jaartijdvak", "Opleidingcode", "Leertraject"])
    )


## Onder deze noemer tonen we geen percentage (privacy en betrouwbaarheid).
MIN_NOEMER = 12
GROEPEN = {
    "instelling": [],
    "niveau": ["Niveau"],
    "opleiding": ["Opleidingcode", "Niveau"],
    "opleiding_leerweg": ["Opleidingcode", "Niveau", "Leertraject"],
}
_JAREN = {"jr": _jaren_jr_dr, "dr": _jaren_jr_dr, "sr": _jaren_sr}


def waarneembare_jaren(indicator: str, w: Waarneming) -> list[int]:
    """Jaartijdvakken t waarvoor de indicator te berekenen is."""
    return _JAREN[indicator](w)


def volledig(indicator: str, w: Waarneming, t: int) -> bool:
    """Is het cijfer van jaartijdvak t volledig (ondergrens of verkorte terugblik)?"""
    if indicator == "dr":
        return dr_volledig(w, t)
    if indicator == "sr":
        return sr_terugblik(w, t) == STARTERS_JAREN_TERUG
    return True


def _label(t: int) -> str:
    return f"{t}-{t + 1}"


def driejaarscijfer(
    eenjaars: pl.DataFrame, indicator: str, w: Waarneming, groep: str
) -> pl.DataFrame:
    """Driejaarscijfer per groep en norm (ontwerp §5.4, regeling art. 4 lid 2).

    ``eenjaars`` is de uitvoer van jaar-, diploma- of startersresultaat.
    Voor elk jaartijdvak t waarvan t-2, t-1 en t waarneembaar zijn, tellen we de
    tellers en noemers van die drie jaren op. Een jaar zonder studenten in de
    groep telt als 0/0. ``indicator`` is ``"jr"``, ``"dr"`` of ``"sr"``;
    ``groep`` een sleutel van [GROEPEN].
    """
    if groep not in GROEPEN:
        raise ValueError(f"Onbekende groep: {groep!r}")
    sleutel = GROEPEN[groep]
    jaren = set(waarneembare_jaren(indicator, w))
    delen = []
    for t in sorted(jaren):
        if not {t - 2, t - 1} <= jaren:
            continue
        venster = eenjaars.filter(pl.col("Jaartijdvak").is_between(t - 2, t))
        som = [pl.col("Teller").sum(), pl.col("Noemer").sum()]
        deel = venster.group_by(sleutel).agg(som) if sleutel else venster.select(som)
        delen.append(
            deel.with_columns(
                pl.lit(t, dtype=pl.Int32).alias("Jaartijdvak"),
                pl.lit(f"{_label(t - 2)} t/m {_label(t)}").alias("Periode"),
                pl.lit(all(volledig(indicator, w, y) for y in (t - 2, t - 1, t))).alias(
                    "Volledig"
                ),
            )
        )
    schema = {
        "Opleidingcode": pl.Utf8,
        "Niveau": pl.Int32,
        "Leertraject": pl.Utf8,
    }
    if not delen:
        delen = [
            pl.DataFrame(
                schema={
                    **{k: v for k, v in schema.items() if k in sleutel},
                    "Teller": pl.Int64,
                    "Noemer": pl.Int64,
                    "Jaartijdvak": pl.Int32,
                    "Periode": pl.Utf8,
                    "Volledig": pl.Boolean,
                }
            )
        ]
    normen = {n: norm_voor(indicator, n, "voldoende") for n in NIVEAUS}
    niveau = pl.col("Niveau") if "Niveau" in sleutel else pl.lit(None, pl.Int32)
    percentage = pl.col("Teller") / pl.col("Noemer") * 100
    return (
        pl.concat(delen)
        .filter(pl.col("Noemer") > 0)
        .with_columns(
            *(
                pl.lit(None, dtype).alias(naam)
                for naam, dtype in schema.items()
                if naam not in sleutel
            ),
            pl.lit(indicator.upper()).alias("Indicator"),
            pl.lit(groep).alias("Groep"),
            percentage.round(1).alias("Percentage"),
            niveau.replace_strict(normen, default=None, return_dtype=pl.Int64).alias(
                "Norm"
            ),
            (pl.col("Noemer") < MIN_NOEMER).alias("Te_klein"),
        )
        .with_columns((percentage < pl.col("Norm")).alias("Onder_norm"))
        .select(
            "Indicator",
            "Jaartijdvak",
            "Periode",
            "Groep",
            *schema,
            "Teller",
            "Noemer",
            "Percentage",
            "Norm",
            "Onder_norm",
            "Te_klein",
            "Volledig",
        )
        .sort(["Jaartijdvak", *sleutel], nulls_last=True)
    )
