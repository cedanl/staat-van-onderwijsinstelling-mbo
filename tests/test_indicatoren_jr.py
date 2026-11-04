from datetime import date

import polars as pl

from staat_mbo.indicatoren import jaarresultaat
from tests.maak import diplomas, peilmomenten, waarneming

A = ("25498", 2, "BOL")
B = ("25475", 3, "BOL")


def _p(persoon, jaar, opleiding=A):
    return (persoon, jaar, *opleiding)


def _uitslag(pm, dip, w, jaartijdvak, crebo):
    rij = (
        jaarresultaat(pm, dip, w)
        .filter(
            (pl.col("Jaartijdvak") == jaartijdvak) & (pl.col("Opleidingcode") == crebo)
        )
        .to_dicts()
    )
    assert len(rij) <= 1
    return (rij[0]["Teller"], rij[0]["Noemer"]) if rij else None


def _scenario():
    pm = peilmomenten(
        [
            _p("s1", 2022),
            _p("s2", 2022),
            _p("s3", 2022),
            _p("s3", 2023),
            _p("s5", 2022),
            _p("s6", 2022),
            _p("s7", 2022),
            _p("s7", 2023, B),
        ]
    )
    dip = diplomas(
        [
            ("s1", "25498", 2, date(2023, 6, 30)),
            ("s4", "25498", 2, date(2023, 7, 1)),
            ("s5", "25498", 2, date(2023, 9, 15)),
            ("s6", "25498", 2, date(2023, 10, 1)),
            ("s7", "25498", 2, date(2023, 6, 30)),
        ]
    )
    return pm, dip


def test_jaarresultaat_teller_en_noemer_van_het_voorbeeld():
    pm, dip = _scenario()
    # Teller: s1, s4 (instroom na 1 oktober), s5, s7 (gestapeld).
    # Noemer: + s2 (weg zonder diploma) en s6 (diploma valt in 2023).
    assert _uitslag(pm, dip, waarneming(2018, 2025), 2022, "25498") == (4, 6)


def test_jaarresultaat_blijver_zonder_diploma_telt_niet_mee():
    pm, dip = _scenario()
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025))
    # s3 staat op 1-10-2023 nog ingeschreven en heeft geen diploma: buiten de noemer.
    assert uit.filter(pl.col("Jaartijdvak") == 2022)["Noemer"].sum() == 6


def test_jaarresultaat_diploma_op_1_oktober_valt_in_het_nieuwe_jaartijdvak():
    pm = peilmomenten([_p("s6", 2022)])
    dip = diplomas([("s6", "25498", 2, date(2023, 10, 1))])
    w = waarneming(2018, 2025)
    # Weg zonder diploma in 2022; het diploma van 2023-10-01 hoort bij 2023.
    assert _uitslag(pm, dip, w, 2022, "25498") == (0, 1)
    assert _uitslag(pm, dip, w, 2023, "25498") == (1, 1)


def test_jaarresultaat_stapelaar_telt_een_keer_voor_het_laatste_diploma():
    pm = peilmomenten([_p("s8", 2022)])
    dip = diplomas(
        [
            ("s8", "25498", 2, date(2022, 12, 1)),
            ("s8", "25475", 3, date(2023, 7, 1)),
        ]
    )
    w = waarneming(2018, 2025)
    assert _uitslag(pm, dip, w, 2022, "25475") == (1, 1)
    assert _uitslag(pm, dip, w, 2022, "25498") is None


def test_jaarresultaat_diploma_krijgt_leertraject_en_niveau_van_het_diploma():
    pm = peilmomenten([_p("s1", 2022)])
    dip = diplomas([("s1", "25475", 3, date(2023, 6, 1))], leertraject="BBL")
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025)).to_dicts()
    assert uit == [
        {
            "Jaartijdvak": 2022,
            "Opleidingcode": "25475",
            "Niveau": 3,
            "Leertraject": "BBL",
            "Teller": 1,
            "Noemer": 1,
        }
    ]


def test_jaarresultaat_entree_valt_buiten_de_populatie():
    pm = peilmomenten(
        [("e1", 2022, "25250", 1, "BOL"), ("e2", 2022, "25250", 1, "BOL")]
    )
    dip = diplomas([("e1", "25250", 1, date(2023, 6, 30))])
    assert jaarresultaat(pm, dip, waarneming(2018, 2025)).is_empty()


def test_jaarresultaat_ovo_valt_buiten_de_populatie():
    pm = peilmomenten(
        [("o1", 2022, "25498", 2, "OVO"), ("o2", 2022, "25498", 2, "OVO")]
    )
    dip = diplomas([("o1", "25498", 2, date(2023, 6, 30))], leertraject="OVO")
    assert jaarresultaat(pm, dip, waarneming(2018, 2025)).is_empty()


def test_jaarresultaat_extraneus_telt_mee():
    pm = peilmomenten([("x1", 2022, "25498", 2, "EX")])
    dip = diplomas([("x1", "25498", 2, date(2023, 6, 30))], leertraject="EX")
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025))
    assert uit["Teller"].to_list() == [1]


def test_jaarresultaat_laatste_jaartijdvak_is_niet_waarneembaar():
    pm, dip = _scenario()
    pm = pm.vstack(peilmomenten([_p("z1", 2025)]))
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025))
    assert 2025 not in uit["Jaartijdvak"].to_list()


def test_jaarresultaat_gat_haalt_de_jaren_eromheen_weg():
    pm = peilmomenten([_p("g1", t) for t in (2021, 2022, 2023, 2024)])
    dip = diplomas([("g1", "25498", 2, date(2021, 12, 1))])
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025, gaten=[2023]))
    jaren = set(uit["Jaartijdvak"].to_list())
    assert 2022 not in jaren and 2023 not in jaren
    assert 2021 in jaren


def test_jaarresultaat_verlater_met_onbekend_niveau_telt_niet():
    pm = peilmomenten([("n1", 2022, "99999", None, "BOL")])
    assert jaarresultaat(pm, diplomas([]), waarneming(2018, 2025)).is_empty()


def test_jaarresultaat_heeft_het_afgesproken_schema():
    pm, dip = _scenario()
    uit = jaarresultaat(pm, dip, waarneming(2018, 2025))
    assert uit.columns == [
        "Jaartijdvak",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "Teller",
        "Noemer",
    ]
