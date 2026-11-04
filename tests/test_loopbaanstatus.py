from datetime import date

import polars as pl

from staat_mbo.cohorten import CATEGORIEEN, loopbaanstatus, uitval
from tests.maak import diplomas, peilmomenten, waarneming

A = ("25498", 2, "BOL")
W = waarneming(2016, 2025)


def _cohort(*personen, niveau=2, crebo="25498", jaar=2020):
    return pl.DataFrame(
        [
            {
                "_persoon_id": p,
                "Cohort": jaar,
                "Opleidingcode": crebo,
                "Niveau": niveau,
                "Leertraject": "BOL",
                "Herkomst": "nieuw",
                "Terugblik": 4,
            }
            for p in personen
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


def _scenario():
    """Eén student per categorie, cohort 2020 op niveau 2, k = 1."""
    personen = [f"c{i}" for i in range(1, 9)]
    pm = peilmomenten(
        [
            ("c1", 2021, "25475", 3, "BOL"),
            ("c3", 2021, "25225", 2, "BOL"),
            ("c4", 2021, "25498", 2, "BOL"),
            ("c5", 2021, "25225", 2, "BOL"),
            ("c6", 2021, "25475", 3, "BOL"),
            ("c7", 2021, "25250", 1, "BOL"),
        ]
    )
    dip = diplomas([(p, "25498", 2, date(2021, 6, 30)) for p in ("c1", "c2", "c3")])
    return _cohort(*personen), pm, dip


def _status(cohort, pm, dip, k=1, w=W):
    uit = loopbaanstatus(cohort, pm, dip, w, k)
    return dict(zip(uit["_persoon_id"], uit["Status"], strict=True))


def test_negen_categorieen_in_vaste_volgorde():
    assert CATEGORIEEN == [
        "Diploma, verder op hoger niveau",
        "Diploma, vertrokken",
        "Diploma, nog ingeschreven op hetzelfde of lager niveau",
        "Zonder diploma, zelfde opleiding",
        "Zonder diploma, ander crebo op hetzelfde niveau",
        "Zonder diploma, hoger niveau",
        "Zonder diploma, lager niveau",
        "Vertrokken zonder diploma",
        "Nog niet waarneembaar",
    ]


def test_elke_categorie_krijgt_zijn_student():
    cohort, pm, dip = _scenario()
    status = _status(cohort, pm, dip)
    assert [status[f"c{i}"] for i in range(1, 9)] == CATEGORIEEN[:8]


def test_nog_niet_waarneembaar():
    cohort, pm, dip = _scenario()
    status = _status(cohort, pm, dip, w=waarneming(2016, 2020))
    assert set(status.values()) == {"Nog niet waarneembaar"}


def test_elke_cohortrij_krijgt_precies_een_categorie():
    cohort, pm, dip = _scenario()
    uit = loopbaanstatus(cohort, pm, dip, W, 1)
    assert uit.height == cohort.height
    assert uit["Status"].is_in(CATEGORIEEN).all()
    assert uit.columns == [*cohort.columns, "Jaren", "Status"]
    assert set(uit["Jaren"]) == {1}


def test_diploma_na_de_peildatum_telt_nog_niet():
    cohort = _cohort("s")
    dip = diplomas([("s", "25498", 2, date(2021, 10, 1))])
    pm = peilmomenten([("s", 2021, "25498", 2, "BOL")])
    assert _status(cohort, pm, dip)["s"] == "Zonder diploma, zelfde opleiding"


def test_diploma_van_voor_het_cohort_telt_niet():
    cohort = _cohort("s")
    dip = diplomas([("s", "25498", 2, date(2020, 9, 30))])
    assert _status(cohort, peilmomenten([]), dip)["s"] == "Vertrokken zonder diploma"


def test_entreediploma_telt_als_diploma():
    cohort = _cohort("s", niveau=1, crebo="25250")
    dip = diplomas([("s", "25250", 1, date(2021, 6, 30))])
    assert _status(cohort, peilmomenten([]), dip)["s"] == "Diploma, vertrokken"


def test_loopbaanstatus_na_twee_jaar_kijkt_naar_de_tweede_peildatum():
    cohort = _cohort("s")
    pm = peilmomenten([("s", 2022, "25475", 3, "BOL")])
    assert _status(cohort, pm, diplomas([]), k=2)["s"] == "Zonder diploma, hoger niveau"
    assert _status(cohort, pm, diplomas([]), k=1)["s"] == "Vertrokken zonder diploma"


def test_opvolger_is_dezelfde_opleiding():
    cohort = _cohort("s")
    pm = peilmomenten([("s", 2021, "25999", 2, "BOL")])
    uit = loopbaanstatus(cohort, pm, diplomas([]), W, 1, opvolgers={"25498": "25999"})
    assert uit["Status"].to_list() == ["Zonder diploma, zelfde opleiding"]


def test_uitval_na_een_jaar_is_vertrokken_zonder_diploma():
    cohort, pm, dip = _scenario()
    uit = uitval(cohort, pm, dip, W, 1)
    assert dict(zip(uit["_persoon_id"], uit["Uitval"], strict=True)) == {
        "c1": False,
        "c2": False,  # diploma, vertrokken: geen uitval
        "c3": False,
        "c4": False,
        "c5": False,
        "c6": False,
        "c7": False,
        "c8": True,
    }
    assert uit.columns == [*cohort.columns, "Jaren", "Uitval"]


def test_wie_terugkomt_is_op_dat_moment_niet_uitgevallen():
    cohort = _cohort("s")
    pm = peilmomenten([("s", 2022, "25498", 2, "BOL")])
    assert uitval(cohort, pm, diplomas([]), W, 1)["Uitval"].to_list() == [True]
    assert uitval(cohort, pm, diplomas([]), W, 2)["Uitval"].to_list() == [False]


def test_uitval_nog_niet_waarneembaar_is_null():
    cohort = _cohort("s")
    uit = uitval(cohort, peilmomenten([]), diplomas([]), waarneming(2016, 2020), 1)
    assert uit["Uitval"].to_list() == [None]


def test_uitval_diploma_laat_de_student_buiten_de_uitval():
    cohort = _cohort("s")
    dip = diplomas([("s", "25498", 2, date(2021, 9, 30))])
    assert uitval(cohort, peilmomenten([]), dip, W, 1)["Uitval"].to_list() == [False]
    dip = diplomas([("s", "25498", 2, date(2021, 10, 1))])
    assert uitval(cohort, peilmomenten([]), dip, W, 1)["Uitval"].to_list() == [True]
