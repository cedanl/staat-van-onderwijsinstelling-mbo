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
        cohort.join(zichtbaar, on=["Cohort", "Duur"], how="left")
        .join(eerste, on="_r", how="left")
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


def _percentage(vlag: str) -> pl.Expr:
    """Percentage True van de waarneembare (niet-null) rijen; null zonder rijen."""
    waarneembaar = pl.col(vlag).drop_nulls()
    return (
        pl.when(waarneembaar.len() > 0)
        .then(waarneembaar.sum() / waarneembaar.len() * 100)
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
            _percentage("Nominaal").alias("Nominaal_percentage"),
            pl.col("Nominaal_plus_1")
            .sum()
            .cast(pl.Int64)
            .alias("Nominaal_plus_1_aantal"),
            _percentage("Nominaal_plus_1").alias("Nominaal_plus_1_percentage"),
            pl.col("In_eigen_opleiding").sum().cast(pl.Int64).alias("In_eigen_aantal"),
            pl.col("Nominaal")
            .is_null()
            .sum()
            .cast(pl.Int64)
            .alias("Nog_niet_waarneembaar"),
        )
        .sort(per)
    )
