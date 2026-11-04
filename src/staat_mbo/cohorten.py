"""Instroomcohorten, rendement, uitval en loopbaanstatus (ontwerp §5.5)."""

import polars as pl
from mbo_bekostiging_bestanden.waardenlijsten import (
    leertrajecten_buiten_indicatorpopulatie,
)

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
