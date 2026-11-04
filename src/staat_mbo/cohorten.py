"""Instroomcohorten, rendement, uitval en loopbaanstatus (ontwerp §5.5)."""

import polars as pl
from mbo_bekostiging_bestanden.waardenlijsten import (
    leertrajecten_buiten_indicatorpopulatie,
)

from staat_mbo.duur import duur_per_opleiding
from staat_mbo.indicatoren import sr_terugblik
from staat_mbo.loopbaan import canoniek, eerste_peiljaar
from staat_mbo.waarneming import Waarneming

_P = "_persoon_id"
_OPLEIDING = ["Opleidingcode", "Leertraject"]
HERKOMSTEN = [
    "nieuw",
    "na diploma",
    "ander niveau zonder diploma",
    "wissel",
]
COHORT = [
    _P,
    "Cohort",
    "Opleidingcode",
    "Niveau",
    "Leertraject",
    "Herkomst",
    "Terugblik",
]


def instroomcohorten(
    pm: pl.DataFrame,
    dip: pl.DataFrame,
    w: Waarneming,
    opvolgers: dict[str, str] | None = None,
) -> pl.DataFrame:
    """Eén rij per persoon × opleiding (crebo × leerweg) met het instroomjaar.

    Het cohort is het eerste jaar waarin de persoon met dit crebo en deze
    leerweg op 1 oktober staat, mits de opleiding in dat jaar begon. Wie al
    eerder begon dan we kunnen waarnemen, valt buiten de cohorten (links
    afgekapt). Rijen zonder niveau of in OVO/ODT doen niet mee. ``Herkomst``:
    nieuw (SR-definitie, zonder diploma en zonder inschrijving in de
    terugblik), na diploma, ander niveau zonder diploma, of wissel.
    ``Terugblik`` is het aantal bekeken jaren (zie [sr_terugblik]).
    """
    pm = canoniek(pm, opvolgers)
    populatie = pm.filter(
        pl.col("Niveau").is_not_null()
        & ~pl.col("Leertraject").is_in(leertrajecten_buiten_indicatorpopulatie())
    )
    cohort = (
        populatie.sort("Jaar")
        .unique([_P, *_OPLEIDING], keep="first", maintain_order=True)
        .filter(
            (eerste_peiljaar(pl.col("DatumBegin")) == pl.col("Jaar"))
            & (pl.col("Jaar") >= w.eerste_jaar)
        )
        .select(
            _P,
            pl.col("Jaar").alias("Cohort"),
            *_OPLEIDING[:1],
            "Niveau",
            "Leertraject",
        )
        .with_row_index("_r")
    )
    jaren = cohort["Cohort"].unique().to_list()
    k = {t: sr_terugblik(w, t) for t in jaren}
    cohort = cohort.with_columns(
        pl.col("Cohort")
        .replace_strict(k, return_dtype=pl.Int32, default=0)
        .alias("Terugblik")
    )
    # Diploma in de terugblik, vóór 1 oktober van het cohortjaar.
    met_diploma = (
        cohort.join(dip.select(_P, "Datum"), on=_P)
        .filter(
            (pl.col("Datum") < pl.date(pl.col("Cohort"), 10, 1))
            & (
                pl.col("Datum")
                >= pl.date(pl.col("Cohort") - pl.col("Terugblik"), 10, 1)
            )
        )
        .select("_r")
        .unique()
        .with_columns(pl.lit(True).alias("_diploma"))
    )
    # De laatste inschrijving in de terugblik.
    vorige = (
        cohort.join(
            pm.select(_P, pl.col("Jaar").alias("_s"), pl.col("Niveau").alias("_vn")),
            on=_P,
        )
        .filter(
            (pl.col("_s") < pl.col("Cohort"))
            & (pl.col("_s") >= pl.col("Cohort") - pl.col("Terugblik"))
        )
        .sort("_s", descending=True)
        .unique("_r", keep="first")
        .select("_r", "_vn")
        .with_columns(pl.lit(True).alias("_eerder"))
    )
    return (
        cohort.join(met_diploma, on="_r", how="left")
        .join(vorige, on="_r", how="left")
        .with_columns(
            pl.when(pl.col("_diploma"))
            .then(pl.lit("na diploma"))
            .when(pl.col("_eerder") & (pl.col("_vn") != pl.col("Niveau")))
            .then(pl.lit("ander niveau zonder diploma"))
            .when(pl.col("_eerder"))
            .then(pl.lit("wissel"))
            .otherwise(pl.lit("nieuw"))
            .alias("Herkomst")
        )
        .select(COHORT)
    )


def rendement(
    cohorten: pl.DataFrame,
    dip: pl.DataFrame,
    duur: pl.DataFrame,
    w: Waarneming,
    opvolgers: dict[str, str] | None = None,
) -> pl.DataFrame:
    """Rendement per cohortrij: nominaal en nominaal + 1 (ontwerp §5.5).

    Een diploma op minstens het instroomniveau, vanaf 1-10-t en uiterlijk
    30-9-(t + duur) (resp. + 1), telt als rendement. ``duur`` is de uitvoer van
    ``nominale_duur``; zonder eigen duur geldt de standaardduur van het niveau.
    Is de periode nog niet (volledig) waarneembaar, dan is de uitkomst null.
    ``In_eigen_opleiding``: het diploma is van hetzelfde crebo (of zijn
    opvolger); null als nominaal null is.
    """
    dip = canoniek(dip, opvolgers)
    cohorten = canoniek(cohorten, opvolgers)
    opleidingen = cohorten.select(*_OPLEIDING, "Niveau").unique(
        _OPLEIDING, keep="first", maintain_order=True
    )
    duren = duur_per_opleiding(
        canoniek(duur, opvolgers).unique(_OPLEIDING, keep="first"), opleidingen
    ).select(*_OPLEIDING, "Duur", "Duur_bron")
    cohort = cohorten.join(duren, on=_OPLEIDING, how="left").with_row_index("_r")
    zichtbaar = pl.DataFrame(
        [
            {
                "Cohort": t,
                "Duur": d,
                "_n": w.reeks(t, t + d),
                "_n1": w.reeks(t, t + d + 1),
            }
            for t, d in cohort.select("Cohort", "Duur").drop_nulls().unique().rows()
        ],
        schema={
            "Cohort": pl.Int32,
            "Duur": pl.Int32,
            "_n": pl.Boolean,
            "_n1": pl.Boolean,
        },
    )
    kandidaten = (
        cohort.select("_r", _P, "Cohort", "Opleidingcode", "Niveau")
        .join(
            dip.select(
                _P,
                "Datum",
                pl.col("Niveau").alias("_dn"),
                pl.col("Opleidingcode").alias("_dc"),
            ),
            on=_P,
        )
        .filter(
            (pl.col("_dn") >= pl.col("Niveau"))
            & (pl.col("Datum") >= pl.date(pl.col("Cohort"), 10, 1))
        )
    )
    eerste = kandidaten.group_by("_r").agg(
        pl.col("Datum").min().alias("_eerste"),
        pl.col("Datum")
        .filter(pl.col("_dc") == pl.col("Opleidingcode"))
        .min()
        .alias("_eigen"),
    )
    nominaal = pl.date(pl.col("Cohort") + pl.col("Duur"), 9, 30)
    plus_1 = pl.date(pl.col("Cohort") + pl.col("Duur") + 1, 9, 30)
    return (
        cohort.join(zichtbaar, on=["Cohort", "Duur"], how="left", maintain_order="left")
        .join(eerste, on="_r", how="left", maintain_order="left")
        ## Elke rij hoort bij dezelfde rij van ``cohorten`` (analyse leunt daarop).
        .sort("_r")
        .with_columns(
            pl.when(pl.col("_n"))
            .then((pl.col("_eerste") <= nominaal).fill_null(False))
            .alias("Nominaal"),
            pl.when(pl.col("_n1"))
            .then((pl.col("_eerste") <= plus_1).fill_null(False))
            .alias("Nominaal_plus_1"),
            pl.when(pl.col("_n"))
            .then((pl.col("_eigen") <= nominaal).fill_null(False))
            .alias("In_eigen_opleiding"),
        )
        .select(
            *cohorten.columns,
            "Duur",
            "Duur_bron",
            "Nominaal",
            "Nominaal_plus_1",
            "In_eigen_opleiding",
        )
    )


def percentage_waar(vlag: str) -> pl.Expr:
    """Percentage True, alleen als elke rij van de groep waarneembaar is.

    Is een deel nog null (bv. een cohort met korte opleidingen die al
    waarneembaar zijn en lange die dat nog niet zijn), dan null: anders
    vergelijkt het percentage een andere populatie dan eerdere cohorten.
    """
    kolom = pl.col(vlag)
    return (
        pl.when((kolom.len() > 0) & (kolom.null_count() == 0))
        .then(kolom.sum() / kolom.len() * 100)
        .round(1)
    )


def rendement_per_groep(df: pl.DataFrame, per: list[str] | None = None) -> pl.DataFrame:
    """Aantallen en percentages van [rendement] per groep (standaard per cohort × opleiding).

    Rijen die nog niet waarneembaar zijn (null) tellen niet mee in het
    percentage; ze staan apart in ``Nog_niet_waarneembaar``.
    """
    per = per or ["Cohort", "Opleidingcode", "Niveau", "Leertraject"]
    return (
        df.group_by(per, maintain_order=True)
        .agg(
            pl.col("Duur").first(),
            pl.col("Duur_bron").first(),
            pl.len().cast(pl.Int64).alias("Instroom"),
            pl.col("Nominaal").sum().cast(pl.Int64).alias("Nominaal_aantal"),
            percentage_waar("Nominaal").alias("Nominaal_percentage"),
            pl.col("Nominaal_plus_1")
            .sum()
            .cast(pl.Int64)
            .alias("Nominaal_plus_1_aantal"),
            percentage_waar("Nominaal_plus_1").alias("Nominaal_plus_1_percentage"),
            pl.col("In_eigen_opleiding").sum().cast(pl.Int64).alias("In_eigen_aantal"),
            pl.col("Nominaal")
            .is_null()
            .sum()
            .cast(pl.Int64)
            .alias("Nog_niet_waarneembaar"),
        )
        .sort(per)
    )


## De negen uitkomsten van de loopbaanstatus, in vaste volgorde (ontwerp §5.5).
CATEGORIEEN = [
    "Diploma, verder op hoger niveau",
    "Diploma, vertrokken",
    "Diploma, nog ingeschreven op hetzelfde of lager niveau",
    "Zonder diploma, zelfde opleiding",
    "Zonder diploma, ander crebo op hetzelfde niveau",
    "Zonder diploma, hoger niveau",
    "Zonder diploma, lager niveau",
    "Vertrokken zonder diploma",
    "Nog niet waarneembaar",
]


def _stand_na(
    cohorten: pl.DataFrame,
    pm: pl.DataFrame,
    dip: pl.DataFrame,
    w: Waarneming,
    k: int,
) -> pl.DataFrame:
    """Per cohortrij: waarneembaar, diploma sinds 1-10-t, en de inschrijving op 1-10-(t+k)."""
    cohort = cohorten.with_columns(
        (pl.col("Cohort") + k).alias("_j"),
        pl.col("Cohort")
        .map_elements(lambda t: w.reeks(t, t + k), return_dtype=pl.Boolean)
        .alias("_zichtbaar"),
    ).with_row_index("_r")
    diploma = (
        cohort.select("_r", _P, "Cohort")
        .join(dip.select(_P, "Datum"), on=_P)
        .filter(
            (pl.col("Datum") >= pl.date(pl.col("Cohort"), 10, 1))
            & (pl.col("Datum") < pl.date(pl.col("Cohort") + k, 10, 1))
        )
        .select("_r")
        .unique()
        .with_columns(pl.lit(True).alias("_diploma"))
    )
    stand = pm.select(
        _P,
        pl.col("Jaar").alias("_j"),
        pl.col("Niveau").alias("_n"),
        pl.col("Opleidingcode").alias("_c"),
        pl.lit(True).alias("_aanwezig"),
    )
    return (
        cohort.join(diploma, on="_r", how="left")
        .join(stand, on=[_P, "_j"], how="left")
        .with_columns(
            pl.col("_diploma").fill_null(False),
            pl.col("_aanwezig").fill_null(False),
        )
    )


def loopbaanstatus(
    cohorten: pl.DataFrame,
    pm: pl.DataFrame,
    dip: pl.DataFrame,
    w: Waarneming,
    k: int,
    opvolgers: dict[str, str] | None = None,
) -> pl.DataFrame:
    """Loopbaanstatus na ``k`` jaar per cohortrij, één van [CATEGORIEEN].

    Gemeten op 1-10-(t+k). Diploma: een mbo-diploma van welk niveau ook, van
    1-10-t tot 1-10-(t+k). Stapelen, op- en afstromen zijn geen studiewissel;
    alleen "Zonder diploma, ander crebo op hetzelfde niveau" is dat.
    """
    cohorten = canoniek(cohorten, opvolgers)
    s = _stand_na(cohorten, canoniek(pm, opvolgers), dip, w, k)
    niveau = pl.col("Niveau")
    hoger = (pl.col("_n") > niveau).fill_null(False)
    lager = (pl.col("_n") < niveau).fill_null(False)
    status = (
        pl.when(~pl.col("_zichtbaar"))
        .then(pl.lit(CATEGORIEEN[8]))
        .when(pl.col("_diploma") & pl.col("_aanwezig") & hoger)
        .then(pl.lit(CATEGORIEEN[0]))
        .when(pl.col("_diploma") & ~pl.col("_aanwezig"))
        .then(pl.lit(CATEGORIEEN[1]))
        .when(pl.col("_diploma"))
        .then(pl.lit(CATEGORIEEN[2]))
        .when(~pl.col("_aanwezig"))
        .then(pl.lit(CATEGORIEEN[7]))
        .when(pl.col("_c") == pl.col("Opleidingcode"))
        .then(pl.lit(CATEGORIEEN[3]))
        .when(hoger)
        .then(pl.lit(CATEGORIEEN[5]))
        .when(lager)
        .then(pl.lit(CATEGORIEEN[6]))
        .otherwise(pl.lit(CATEGORIEEN[4]))
    )
    return s.sort("_r").select(
        *cohorten.columns,
        pl.lit(k, dtype=pl.Int32).alias("Jaren"),
        status.alias("Status"),
    )


def uitval(
    cohorten: pl.DataFrame,
    pm: pl.DataFrame,
    dip: pl.DataFrame,
    w: Waarneming,
    x: int,
    opvolgers: dict[str, str] | None = None,
) -> pl.DataFrame:
    """Uitval na ``x`` jaar per cohortrij: een status op 1-10-(t+x), geen cumulatief cijfer.

    Uitgevallen: niet ingeschreven op 1-10-(t+x) en sinds 1-10-t geen
    mbo-diploma (entree inbegrepen). Wie terugkomt is niet uitgevallen. Null als
    de periode nog niet (volledig) waarneembaar is.

    Het ontwerp noemt als venster het einde 30-9-(t+x-1); dat sluit het jaar
    voor 1-10-(t+x) uit. Hier loopt het venster tot 30-9-(t+x), net als bij
    de loopbaanstatus, zodat een diploma in dat jaar de student uit de uitval houdt.
    """
    cohorten = canoniek(cohorten, opvolgers)
    s = _stand_na(cohorten, pm, dip, w, x)
    uit = (
        pl.when(~pl.col("_zichtbaar"))
        .then(None)
        .otherwise(~pl.col("_aanwezig") & ~pl.col("_diploma"))
    )
    return s.sort("_r").select(
        *cohorten.columns, pl.lit(x, dtype=pl.Int32).alias("Jaren"), uit.alias("Uitval")
    )
