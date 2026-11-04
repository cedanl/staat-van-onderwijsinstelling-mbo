"""Mbo-tussenlaag: peilmomenten en diploma's per persoon (ontwerp §4)."""

import polars as pl
from mbo_bekostiging_bestanden.opleidingsniveau import vul_niveau_aan

_P = "_persoon_id"


def eerste_peiljaar(datum: pl.Expr) -> pl.Expr:
    """Schooljaar van de eerste 1 oktober op of na ``datum``."""
    jaar = datum.dt.year()
    return pl.when(datum <= pl.date(jaar, 10, 1)).then(jaar).otherwise(jaar + 1)


def niveau_getal(niveau: pl.Expr) -> pl.Expr:
    """Niveau als getal: ``"MBO-3"`` wordt 3."""
    return niveau.str.extract(r"(\d)").cast(pl.Int32)


def peilmomenten(star: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Eén inschrijving per persoon × 1 oktober, gekozen over alle BRIN's.

    Hoogste niveau (onbekend als laatste), dan laagste crebo, dan recentste
    start, dan hoogste volgnummer. Wie alleen inschrijvingen zonder niveau
    heeft, staat er wel in, met ``Niveau`` null.
    """
    sj = vul_niveau_aan(star["fact_inschrijving_schooljaar"])
    return (
        sj.select(
            _P,
            pl.col("Schooljaar").cast(pl.Int32).alias("Jaar"),
            "BRIN",
            "Inschrijvingvolgnummer",
            "Opleidingcode",
            niveau_getal(pl.col("Niveau")).alias("Niveau"),
            "Leertraject",
            "DatumBegin",
        )
        .sort(
            [
                _P,
                "Jaar",
                "Niveau",
                "Opleidingcode",
                "DatumBegin",
                "Inschrijvingvolgnummer",
            ],
            descending=[False, False, True, False, True, True],
            nulls_last=True,
        )
        .unique([_P, "Jaar"], keep="first", maintain_order=True)
    )
