from datetime import date

import polars as pl

from staat_mbo.cohorten import rendement, rendement_per_groep
from tests.maak import diplomas, waarneming

W = waarneming(2016, 2025)


def _cohort(niveau=2, crebo="25498", jaar=2020, leertraject="BOL"):
    return pl.DataFrame(
        [
            {
                "_persoon_id": "s",
                "Cohort": jaar,
                "Opleidingcode": crebo,
                "Niveau": niveau,
                "Leertraject": leertraject,
                "Herkomst": "nieuw",
                "Terugblik": 4,
            }
        ],
        schema={
            "_persoon_id": pl.Utf8,
            "Cohort": pl.Int32,
            "Opleidingcode": pl.Utf8,
            "Niveau": pl.Int32,
            "Leertraject": pl.Utf8,
            "Herkomst": pl.Utf8,
            "Terugblik": pl.Int32,
        },
    )


def _duur(jaren=2, crebo="25498", leertraject="BOL"):
    return pl.DataFrame(
        {
            "Opleidingcode": [crebo],
            "Leertraject": [leertraject],
            "nominale_duur": [jaren],
        },
        schema_overrides={"nominale_duur": pl.Int32},
    )


def _rij(cohort, dip, duur=None, w=W, **kw):
    uit = rendement(cohort, dip, _duur() if duur is None else duur, w, **kw)
    assert uit.height == 1
    return uit.to_dicts()[0]


def test_diploma_binnen_de_nominale_duur_is_nominaal_en_in_eigen_opleiding():
    rij = _rij(_cohort(), diplomas([("s", "25498", 2, date(2022, 6, 30))]))
    assert rij["Duur"] == 2 and rij["Duur_bron"] == "geplande einddatum"
    assert rij["Nominaal"] is True
    assert rij["Nominaal_plus_1"] is True
    assert rij["In_eigen_opleiding"] is True


def test_diploma_op_30_september_van_het_laatste_jaar_is_nog_nominaal():
    rij = _rij(_cohort(), diplomas([("s", "25498", 2, date(2022, 9, 30))]))
    assert rij["Nominaal"] is True


def test_diploma_op_1_oktober_erna_is_alleen_nominaal_plus_1():
    rij = _rij(_cohort(), diplomas([("s", "25498", 2, date(2022, 10, 1))]))
    assert rij["Nominaal"] is False
    assert rij["Nominaal_plus_1"] is True
    assert rij["In_eigen_opleiding"] is False


def test_diploma_na_nominaal_plus_1_telt_nergens():
    rij = _rij(_cohort(), diplomas([("s", "25498", 2, date(2023, 10, 1))]))
    assert rij["Nominaal"] is False and rij["Nominaal_plus_1"] is False


def test_diploma_van_een_ander_crebo_telt_mee_maar_niet_als_eigen_opleiding():
    rij = _rij(_cohort(), diplomas([("s", "25225", 2, date(2022, 6, 30))]))
    assert rij["Nominaal"] is True
    assert rij["In_eigen_opleiding"] is False


def test_hoger_diploma_telt_mee():
    rij = _rij(_cohort(), diplomas([("s", "25475", 3, date(2022, 6, 30))]))
    assert rij["Nominaal"] is True


def test_afgestroomd_met_een_lager_diploma_is_niet_nominaal():
    cohort = _cohort(niveau=3, crebo="25475")
    dip = diplomas([("s", "25498", 2, date(2022, 6, 30))])
    rij = _rij(cohort, dip, duur=_duur(3, "25475"), w=waarneming(2016, 2025))
    assert rij["Nominaal"] is False


def test_diploma_van_voor_het_cohort_telt_niet():
    rij = _rij(_cohort(), diplomas([("s", "25498", 2, date(2020, 9, 30))]))
    assert rij["Nominaal"] is False


def test_diploma_van_een_andere_persoon_telt_niet():
    rij = _rij(_cohort(), diplomas([("x", "25498", 2, date(2022, 6, 30))]))
    assert rij["Nominaal"] is False


def test_nog_niet_waarneembaar_geeft_null():
    dip = diplomas([("s", "25498", 2, date(2021, 6, 30))])
    kort = _rij(_cohort(), dip, w=waarneming(2016, 2021))
    assert kort["Nominaal"] is None
    assert kort["Nominaal_plus_1"] is None
    assert kort["In_eigen_opleiding"] is None
    een_jaar = _rij(_cohort(), dip, duur=_duur(1), w=waarneming(2016, 2021))
    assert een_jaar["Nominaal"] is True
    assert een_jaar["Nominaal_plus_1"] is None  # 2022 is nog niet te zien


def test_gat_in_de_duur_geeft_null():
    dip = diplomas([("s", "25498", 2, date(2022, 6, 30))])
    rij = _rij(_cohort(), dip, w=waarneming(2016, 2025, gaten=[2021]))
    assert rij["Nominaal"] is None


def test_standaardduur_voor_een_opleiding_zonder_eigen_duur():
    cohort = _cohort(niveau=4, crebo="25655")
    rij = _rij(cohort, diplomas([]), duur=_duur(2))
    assert rij["Duur"] == 4 and rij["Duur_bron"] == "standaard"


def test_opvolger_telt_als_eigen_opleiding():
    dip = diplomas([("s", "25999", 2, date(2022, 6, 30))])
    rij = _rij(_cohort(), dip, opvolgers={"25498": "25999"})
    assert rij["In_eigen_opleiding"] is True


def test_rendement_behoudt_de_cohortkolommen():
    uit = rendement(_cohort(), diplomas([]), _duur(), W)
    assert uit.columns == [
        *_cohort().columns,
        "Duur",
        "Duur_bron",
        "Nominaal",
        "Nominaal_plus_1",
        "In_eigen_opleiding",
    ]


def test_rendement_per_groep_telt_null_niet_mee():
    uit = pl.concat([_cohort()] * 3).with_columns(
        pl.Series("_persoon_id", ["a", "b", "c"])
    )
    dip = diplomas(
        [("a", "25498", 2, date(2022, 6, 30)), ("b", "25498", 2, date(2023, 6, 30))]
    )
    # c blijft niet waarneembaar: geef die rij een cohort in 2024.
    uit = uit.with_columns(
        pl.when(pl.col("_persoon_id") == "c")
        .then(2024)
        .otherwise(2020)
        .alias("Cohort")
        .cast(pl.Int32)
    )
    r = rendement(uit, dip, _duur(), W)
    groep = rendement_per_groep(r, per=["Opleidingcode", "Leertraject"])
    rij = groep.to_dicts()[0]
    assert rij["Instroom"] == 3
    assert rij["Nominaal_aantal"] == 1
    assert rij["Nominaal_percentage"] == 50.0
    assert rij["Nominaal_plus_1_percentage"] == 100.0
    assert rij["Nog_niet_waarneembaar"] == 1
    assert rij["In_eigen_aantal"] == 1


def test_rendement_per_groep_zonder_waarneembare_rijen_geeft_geen_percentage():
    r = rendement(_cohort(), diplomas([]), _duur(), waarneming(2016, 2021))
    rij = rendement_per_groep(r).to_dicts()[0]
    assert rij["Nominaal_percentage"] is None
    assert rij["Nog_niet_waarneembaar"] == 1
