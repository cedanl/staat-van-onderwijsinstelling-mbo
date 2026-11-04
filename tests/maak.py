"""Bouwers voor kleine testframes in het schema van de mbo-tussenlaag."""

from datetime import date

import polars as pl

from staat_mbo.waarneming import Waarneming

PEILMOMENTEN = {
    "_persoon_id": pl.Utf8,
    "Jaar": pl.Int32,
    "BRIN": pl.Utf8,
    "Inschrijvingvolgnummer": pl.Utf8,
    "Opleidingcode": pl.Utf8,
    "Niveau": pl.Int32,
    "Leertraject": pl.Utf8,
    "DatumBegin": pl.Date,
}
DIPLOMAS = {
    "_persoon_id": pl.Utf8,
    "Opleidingcode": pl.Utf8,
    "Niveau": pl.Int32,
    "Leertraject": pl.Utf8,
    "BRIN": pl.Utf8,
    "Datum": pl.Date,
    "Jaartijdvak": pl.Int32,
}


def peilmomenten(
    rijen: list[tuple], brin: str = "27DV", begin: date | None = None
) -> pl.DataFrame:
    """Rijen: (persoon, jaar, crebo, niveau, leertraject).

    ``begin`` is standaard 1 augustus van het jaar.
    """
    return pl.DataFrame(
        [
            {
                "_persoon_id": persoon,
                "Jaar": jaar,
                "BRIN": brin,
                "Inschrijvingvolgnummer": "1",
                "Opleidingcode": crebo,
                "Niveau": niveau,
                "Leertraject": leertraject,
                "DatumBegin": begin or date(jaar, 8, 1),
            }
            for persoon, jaar, crebo, niveau, leertraject in rijen
        ],
        schema=PEILMOMENTEN,
    )


def diplomas(
    rijen: list[tuple], leertraject: str = "BOL", brin: str = "27DV"
) -> pl.DataFrame:
    """Rijen: (persoon, crebo, niveau, datum)."""
    return pl.DataFrame(
        [
            {
                "_persoon_id": persoon,
                "Opleidingcode": crebo,
                "Niveau": niveau,
                "Leertraject": leertraject,
                "BRIN": brin,
                "Datum": datum,
                "Jaartijdvak": datum.year if datum.month >= 10 else datum.year - 1,
            }
            for persoon, crebo, niveau, datum in rijen
        ],
        schema=DIPLOMAS,
    )


def waarneming(eerste: int, laatste: int, gaten: list[int] | None = None):
    """Waarneming van 1 oktober ``eerste`` t/m ``laatste``; diploma's vanaf 1 augustus."""
    return Waarneming(
        eerste_jaar=eerste,
        laatste_jaar=laatste,
        diplomas_vanaf=date(eerste, 8, 1),
        gaten=gaten or [],
    )
