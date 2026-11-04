from datetime import date

import polars as pl

from staat_mbo.duur import (
    MIN_INSCHRIJVINGEN_DUUR,
    duur_per_opleiding,
    nominale_duur,
)


def _geplande_inschrijvingen(crebo, jaren, start=0, leertraject="BOL"):
    """Rijen voor fact_inschrijving: één inschrijving per duur in ``jaren``."""
    return [
        {
            "levering": "RO1",
            "_persoon_id": f"p{start + i}",
            "BRIN": "21CY",
            "Inschrijvingvolgnummer": "1",
            "Opleidingcode": crebo,
            "Leertraject": leertraject,
            "DatumInschrijving": date(2020, 8, 1),
            "DatumUitschrijvingGepland": date(2020 + j, 7, 31),
        }
        for i, j in enumerate(jaren)
    ]


def _duur(rijen):
    return nominale_duur({"fact_inschrijving": pl.DataFrame(rijen)})


def test_nominale_duur_is_meest_voorkomende_geplande_duur():
    # Een paar studenten met verschoven einddatum veranderen de norm niet.
    rijen = _geplande_inschrijvingen("25711", [3] * 8 + [4, 5])
    duur = _duur(rijen)
    assert duur.rows() == [("25711", "BOL", 3)]


def test_nominale_duur_per_leerweg():
    rijen = _geplande_inschrijvingen("25711", [3] * 10) + _geplande_inschrijvingen(
        "25711", [2] * 10, start=100, leertraject="BBL"
    )
    duur = _duur(rijen).sort("Leertraject")
    assert duur.rows() == [("25711", "BBL", 2), ("25711", "BOL", 3)]


def test_nominale_duur_vraagt_genoeg_inschrijvingen():
    rijen = _geplande_inschrijvingen("25711", [3] * (MIN_INSCHRIJVINGEN_DUUR - 1))
    assert _duur(rijen).is_empty()


def test_nominale_duur_telt_inschrijving_een_keer_over_leveringen():
    # Dezelfde 9 inschrijvingen in twee RO's: nog steeds te weinig.
    rijen = _geplande_inschrijvingen("25711", [3] * 9)
    tweede = [{**r, "levering": "RO2"} for r in rijen]
    assert _duur(rijen + tweede).is_empty()


def test_nominale_duur_negeert_inschrijving_met_wissel():
    # De geplande einddatum hoort bij de inschrijving, niet bij de opleiding:
    # wie binnen één inschrijving wisselt, zegt niets over de duur van 25711.
    rijen = _geplande_inschrijvingen("25711", [3] * 10)
    wissel = [{**r, "Opleidingcode": "25916"} for r in rijen]
    assert _duur(rijen + wissel).is_empty()


def _opleidingen(*rijen):
    """Rijen: (crebo, leertraject, niveau)."""
    return pl.DataFrame(
        rijen,
        schema={
            "Opleidingcode": pl.Utf8,
            "Leertraject": pl.Utf8,
            "Niveau": pl.Int32,
        },
        orient="row",
    )


def test_duur_per_opleiding_met_bron():
    duur = pl.DataFrame(
        {"Opleidingcode": ["25711"], "Leertraject": ["BOL"], "nominale_duur": [3]},
        schema={
            "Opleidingcode": pl.Utf8,
            "Leertraject": pl.Utf8,
            "nominale_duur": pl.Int32,
        },
    )
    opleidingen = _opleidingen(("25711", "BOL", 3), ("25916", "BOL", 4))
    uit = duur_per_opleiding(duur, opleidingen).sort("Opleidingcode")
    assert uit.columns == [
        "Opleidingcode",
        "Leertraject",
        "Niveau",
        "Duur",
        "Duur_bron",
    ]
    assert uit.select("Duur", "Duur_bron").rows() == [
        (3, "geplande einddatum"),
        (4, "standaard"),
    ]


def test_duur_per_opleiding_zonder_niveau_en_duur_is_onbekend():
    duur = pl.DataFrame(
        schema={
            "Opleidingcode": pl.Utf8,
            "Leertraject": pl.Utf8,
            "nominale_duur": pl.Int32,
        }
    )
    uit = duur_per_opleiding(duur, _opleidingen(("1", "BOL", None)))
    assert uit.select("Duur", "Duur_bron").rows() == [(None, None)]
