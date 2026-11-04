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


def jaartijdvak(datum: pl.Expr) -> pl.Expr:
    """Jaar waarin het jaartijdvak (1 oktober t/m 30 september) van ``datum`` begint."""
    jaar = datum.dt.year()
    return pl.when(datum.dt.month() >= 10).then(jaar).otherwise(jaar - 1)


def diplomas(star: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Eén rij per persoon × diploma, met het niveau van het diploma zelf.

    Het niveau komt van het crebo van het diploma, niet van de inschrijving:
    een eerder diploma op een lager niveau telt mee. Leerweg en BRIN komen
    van de inschrijving waar het diploma bij hoort.
    """
    niveaus = (
        star["dim_opleiding"]
        .select("Opleidingcode", "Niveau")
        .unique("Opleidingcode", keep="first", maintain_order=True)
    )
    dip = (
        star["fact_inschrijving"]
        .filter(pl.col("DIP_DatumResultaat").is_not_null())
        .select(
            _P,
            pl.col("DIP_Opleidingcode").alias("Opleidingcode"),
            "Leertraject",
            "BRIN",
            pl.col("DIP_DatumResultaat").alias("Datum"),
        )
        .join(niveaus, on="Opleidingcode", how="left")
    )
    return (
        vul_niveau_aan(dip)
        .select(
            _P,
            "Opleidingcode",
            niveau_getal(pl.col("Niveau")).alias("Niveau"),
            "Leertraject",
            "BRIN",
            "Datum",
            jaartijdvak(pl.col("Datum")).cast(pl.Int32).alias("Jaartijdvak"),
        )
        .sort(_P, "Opleidingcode", "Datum", "BRIN", "Leertraject", nulls_last=True)
        .unique([_P, "Opleidingcode", "Datum"], keep="first", maintain_order=True)
    )


def opvolgers(star: dict[str, pl.DataFrame]) -> dict[str, str]:
    """Crebo naar het nieuwste crebo dat het opvolgt, uit ``dim_opleiding``.

    Een lege opvolger, 0 en het eigen crebo betekenen "geen opvolger". Ketens
    (A naar B naar C) lopen door tot het einde; een kring stopt vanzelf.
    """
    dim = star["dim_opleiding"].select(
        pl.col("Opleidingcode").cast(pl.Utf8),
        pl.col("Opleiding_opvolger").cast(pl.Utf8).str.strip_chars().alias("Opvolger"),
    )
    direct = {
        crebo: volger
        for crebo, volger in dim.drop_nulls().iter_rows()
        if volger not in ("", "0", crebo)
    }

    def einde(crebo: str) -> str:
        gezien = {crebo}
        while (volger := direct.get(crebo)) is not None and volger not in gezien:
            crebo = volger
            gezien.add(crebo)
        return crebo

    return {crebo: einde(crebo) for crebo in direct}


def canoniek(df: pl.DataFrame, kaart: dict[str, str] | None) -> pl.DataFrame:
    """Vervang ``Opleidingcode`` door het nieuwste crebo uit ``kaart``."""
    if not kaart:
        return df
    return df.with_columns(pl.col("Opleidingcode").replace(kaart))
