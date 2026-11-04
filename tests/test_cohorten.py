from datetime import date

import polars as pl

from staat_mbo.cohorten import instroomcohorten
from staat_mbo.loopbaan import opvolgers
from tests.maak import diplomas, peilmomenten, waarneming

A = ("25498", 2, "BOL")
B = ("25475", 3, "BOL")
W = waarneming(2016, 2025)
GEEN = diplomas([])


def _cohorten(pm, dip=GEEN, w=W, **kw):
    return instroomcohorten(pm, dip, w, **kw).sort("_persoon_id", "Cohort")


def test_eerste_keer_in_een_opleiding_is_een_nieuwe_instromer():
    pm = peilmomenten([("s", 2020, *A)], begin=date(2020, 8, 15))
    uit = _cohorten(pm).to_dicts()
    assert uit == [
        {
            "_persoon_id": "s",
            "Cohort": 2020,
            "Opleidingcode": "25498",
            "Niveau": 2,
            "Leertraject": "BOL",
            "Herkomst": "nieuw",
            "Terugblik": 4,
        }
    ]


def test_opleiding_die_voor_de_waarneming_begon_hoort_niet_bij_de_cohorten():
    pm = peilmomenten([("s", 2020, *A)], begin=date(2019, 8, 1))
    assert _cohorten(pm, w=waarneming(2020, 2025)).is_empty()


def test_vervolgjaren_van_dezelfde_opleiding_maken_geen_nieuw_cohort():
    pm = peilmomenten(
        [("s", 2020, *A), ("s", 2021, *A), ("s", 2022, *A)], begin=date(2020, 8, 1)
    )
    assert _cohorten(pm)["Cohort"].to_list() == [2020]


def test_start_na_1_oktober_hoort_bij_het_cohort_van_de_eerste_peildatum():
    pm = peilmomenten([("s", 2021, *A)], begin=date(2020, 12, 1))
    assert _cohorten(pm)["Cohort"].to_list() == [2021]


def test_herkomst_na_diploma_is_een_stapelaar():
    pm = peilmomenten([("s", 2020, *A), ("s", 2021, *B)])
    dip = diplomas([("s", "25498", 2, date(2021, 6, 30))])
    uit = _cohorten(pm, dip)
    assert uit["Opleidingcode"].to_list() == ["25498", "25475"]
    assert uit["Herkomst"].to_list() == ["nieuw", "na diploma"]
    assert uit["Cohort"].to_list() == [2020, 2021]


def test_herkomst_entreediploma_telt_ook_als_diploma():
    pm = peilmomenten([("s", 2020, "25250", 1, "BOL"), ("s", 2021, *A)])
    dip = diplomas([("s", "25250", 1, date(2021, 6, 30))])
    assert _cohorten(pm, dip)["Herkomst"].to_list() == ["nieuw", "na diploma"]


def test_herkomst_ander_niveau_zonder_diploma():
    pm = peilmomenten([("s", 2020, *A), ("s", 2021, *B)])
    assert _cohorten(pm)["Herkomst"].to_list() == [
        "nieuw",
        "ander niveau zonder diploma",
    ]


def test_herkomst_afstromen_is_ook_ander_niveau_zonder_diploma():
    pm = peilmomenten([("s", 2020, *B), ("s", 2021, *A)])
    assert _cohorten(pm)["Herkomst"].to_list() == [
        "nieuw",
        "ander niveau zonder diploma",
    ]


def test_herkomst_wissel_op_hetzelfde_niveau():
    pm = peilmomenten([("s", 2020, "25498", 2, "BOL"), ("s", 2021, "25225", 2, "BOL")])
    assert _cohorten(pm)["Herkomst"].to_list() == ["nieuw", "wissel"]


def test_herkomst_leerwegwissel_op_hetzelfde_crebo_is_een_wissel():
    pm = peilmomenten([("s", 2020, "25498", 2, "BOL"), ("s", 2021, "25498", 2, "BBL")])
    assert _cohorten(pm)["Herkomst"].to_list() == ["nieuw", "wissel"]


def test_herkomst_nieuw_als_de_laatste_peildatum_voor_de_terugblik_valt():
    pm = peilmomenten([("s", 2016, *A), ("s", 2023, *B)])
    uit = _cohorten(pm)
    assert uit["Herkomst"].to_list() == ["nieuw", "nieuw"]


def test_terugblik_is_hooguit_zes_en_nul_in_het_eerste_jaar():
    pm = peilmomenten([("a", 2016, *A), ("b", 2025, *A)])
    uit = _cohorten(pm)
    assert uit["Terugblik"].to_list() == [0, 6]


def test_cohortopvolger_geldt_als_dezelfde_opleiding():
    pm = peilmomenten([("s", 2020, "25498", 2, "BOL"), ("s", 2021, "25999", 2, "BOL")])
    zonder = _cohorten(pm)
    met = _cohorten(pm, opvolgers={"25498": "25999"})
    assert zonder.height == 2
    assert met.height == 1
    assert met["Cohort"].to_list() == [2020]
    assert met["Opleidingcode"].to_list() == ["25999"]


def test_opleiding_zonder_niveau_of_in_ovo_doet_niet_mee():
    pm = peilmomenten(
        [
            ("a", 2020, "99999", None, "BOL"),
            ("b", 2020, "25498", 2, "OVO"),
            ("c", 2020, "25498", 2, "ODT"),
            ("d", 2020, "25498", 2, "BOL"),
        ]
    )
    assert _cohorten(pm)["_persoon_id"].to_list() == ["d"]


def test_opvolgers_negeert_eigen_crebo_nul_leeg_en_null():
    dim = pl.DataFrame(
        {
            "Opleidingcode": ["1", "2", "3", "4", "5", "6"],
            "Opleiding_opvolger": [1, 0, None, 9, 5, 7],
        }
    )
    assert opvolgers({"dim_opleiding": dim}) == {"4": "9", "6": "7"}


def test_opvolgers_volgt_een_keten_tot_het_einde():
    dim = pl.DataFrame({"Opleidingcode": ["1", "2"], "Opleiding_opvolger": ["2", "3"]})
    assert opvolgers({"dim_opleiding": dim}) == {"1": "3", "2": "3"}


def test_opvolgers_overleeft_een_kringverwijzing():
    dim = pl.DataFrame({"Opleidingcode": ["1", "2"], "Opleiding_opvolger": ["2", "1"]})
    assert set(opvolgers({"dim_opleiding": dim})) == {"1", "2"}


def test_opvolgers_demodata_is_gevuld(demodata_star):
    ster = demodata_star
    kaart = opvolgers(ster)
    assert kaart  # de demodata heeft echte opvolgers; de test zet niets op xfail
    assert all(k != v for k, v in kaart.items())


def test_instroomcohorten_op_demodata(demodata_star):
    from staat_mbo.loopbaan import diplomas as maak_diplomas
    from staat_mbo.loopbaan import peilmomenten as maak_pm
    from staat_mbo.waarneming import waarneming as maak_w

    ster = demodata_star
    uit = instroomcohorten(
        maak_pm(ster), maak_diplomas(ster), maak_w(ster), opvolgers=opvolgers(ster)
    )
    assert uit.height > 0
    assert uit["Herkomst"].null_count() == 0
    assert (
        uit.select("_persoon_id", "Opleidingcode", "Leertraject").is_duplicated().sum()
        == 0
    )
