from datetime import date

import polars as pl

from tests.maak import diplomas, peilmomenten, waarneming


def test_peilmomenten_heeft_het_schema_uit_het_ontwerp():
    df = peilmomenten([("s1", 2022, "25498", 2, "BOL")])
    assert df.height == 1
    assert df.schema == {
        "_persoon_id": pl.Utf8,
        "Jaar": pl.Int32,
        "BRIN": pl.Utf8,
        "Inschrijvingvolgnummer": pl.Utf8,
        "Opleidingcode": pl.Utf8,
        "Niveau": pl.Int32,
        "Leertraject": pl.Utf8,
        "DatumBegin": pl.Date,
    }
    rij = df.row(0, named=True)
    assert rij["BRIN"] == "27DV"
    assert rij["Inschrijvingvolgnummer"] == "1"
    assert rij["DatumBegin"] == date(2022, 8, 1)


def test_peilmomenten_neemt_afwijkingen_over():
    df = peilmomenten(
        [("s1", 2022, "25498", None, "BBL")],
        brin="21CY",
        begin=date(2021, 9, 1),
    )
    rij = df.row(0, named=True)
    assert (rij["Niveau"], rij["BRIN"], rij["DatumBegin"]) == (
        None,
        "21CY",
        date(2021, 9, 1),
    )


def test_diplomas_heeft_jaartijdvak_en_standaardwaarden():
    df = diplomas([("s1", "25498", 2, date(2023, 6, 30))])
    assert df.schema == {
        "_persoon_id": pl.Utf8,
        "Opleidingcode": pl.Utf8,
        "Niveau": pl.Int32,
        "Leertraject": pl.Utf8,
        "BRIN": pl.Utf8,
        "Datum": pl.Date,
        "Jaartijdvak": pl.Int32,
    }
    rij = df.row(0, named=True)
    assert rij["Jaartijdvak"] == 2022
    assert rij["Leertraject"] == "BOL"
    assert rij["BRIN"] == "27DV"


def test_diplomas_grens_op_1_oktober():
    df = diplomas(
        [
            ("s1", "25498", 2, date(2024, 9, 30)),
            ("s2", "25498", 2, date(2024, 10, 1)),
        ]
    )
    assert df["Jaartijdvak"].to_list() == [2023, 2024]


def test_waarneming_bouwer():
    w = waarneming(2018, 2025)
    assert (w.eerste_jaar, w.laatste_jaar, w.gaten) == (2018, 2025, [])
    assert w.diplomas_vanaf == date(2018, 8, 1)


def test_waarneming_waarneembaar_en_reeks():
    w = waarneming(2018, 2025, gaten=[2022])
    assert w.waarneembaar(2018) is True
    assert w.waarneembaar(2017) is False
    assert w.waarneembaar(2026) is False
    assert w.waarneembaar(2022) is False
    assert w.reeks(2019, 2021) is True
    assert w.reeks(2021, 2023) is False
