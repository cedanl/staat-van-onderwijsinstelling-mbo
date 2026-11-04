"""Nominale duur per opleiding × leerweg, uit de geplande einddatum."""

import polars as pl

from staat_mbo.loopbaan import niveau_getal

_P = "_persoon_id"
## Minimaal aantal inschrijvingen per opleiding × leerweg voor een eigen
## nominale duur; daaronder geldt de standaardduur per niveau.
MIN_INSCHRIJVINGEN_DUUR = 10
## Niveau 4 is meestal 4 jaar (studielast 6400 SBU in RIO), soms 3.
STANDAARDDUUR = {1: 1, 2: 2, 3: 3, 4: 4}


def nominale_duur(star: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Nominale duur in jaren per opleiding × leerweg, uit de geplande einddatum.

    De school kan de geplande einddatum van één student verschuiven bij
    vertraging; daarom de meest voorkomende geplande duur over alle
    inschrijvingen, niet die van de student zelf. De datum hoort bij de
    inschrijving: inschrijvingen met meer dan één opleiding tellen niet mee.
    Bij een gelijke stand de langste duur, zodat niemand onterecht te laat is.
    """
    sleutel = [_P, "BRIN", "Inschrijvingvolgnummer"]
    ins = star["fact_inschrijving"].unique([*sleutel, "Opleidingcode"])
    een_opleiding = ins.filter(pl.col("Opleidingcode").n_unique().over(sleutel) == 1)
    dagen = (
        pl.col("DatumUitschrijvingGepland") - pl.col("DatumInschrijving")
    ).dt.total_days() + 1
    jaren = een_opleiding.drop_nulls(
        ["DatumInschrijving", "DatumUitschrijvingGepland"]
    ).select(
        "Opleidingcode",
        "Leertraject",
        (dagen / 365.25).round().clip(lower_bound=1).cast(pl.Int32).alias("_jaren"),
    )
    return (
        jaren.group_by("Opleidingcode", "Leertraject", "_jaren")
        .len()
        .with_columns(
            pl.col("len").sum().over("Opleidingcode", "Leertraject").alias("_n")
        )
        .filter(pl.col("_n") >= MIN_INSCHRIJVINGEN_DUUR)
        .sort(["len", "_jaren"], descending=True)
        .unique(["Opleidingcode", "Leertraject"], keep="first", maintain_order=True)
        .select("Opleidingcode", "Leertraject", pl.col("_jaren").alias("nominale_duur"))
        .sort("Opleidingcode", "Leertraject")
    )


def duur_per_opleiding(duur: pl.DataFrame, opleidingen: pl.DataFrame) -> pl.DataFrame:
    """Duur en de herkomst ervan per opleiding × leerweg.

    ``duur`` komt uit [nominale_duur]; ``opleidingen`` heeft ``Opleidingcode``,
    ``Leertraject`` en ``Niveau`` (getal of "MBO-n"). Heeft een opleiding geen
    eigen duur, dan geldt de standaardduur van het niveau; kent ook het niveau
    niet, dan zijn ``Duur`` en ``Duur_bron`` null.
    """
    niveau = (
        niveau_getal(pl.col("Niveau"))
        if opleidingen.schema["Niveau"] == pl.Utf8
        else pl.col("Niveau")
    )
    standaard = niveau.replace_strict(
        STANDAARDDUUR, default=None, return_dtype=pl.Int32
    )
    return (
        opleidingen.join(duur, on=["Opleidingcode", "Leertraject"], how="left")
        .with_columns(
            pl.coalesce("nominale_duur", standaard).cast(pl.Int32).alias("Duur"),
            pl.when(pl.col("nominale_duur").is_not_null())
            .then(pl.lit("geplande einddatum"))
            .when(standaard.is_not_null())
            .then(pl.lit("standaard"))
            .alias("Duur_bron"),
        )
        .drop("nominale_duur")
    )
