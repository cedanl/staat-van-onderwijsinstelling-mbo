from datetime import date

from staat_mbo.indicatoren import diplomaresultaat
from tests.maak import diplomas, peilmomenten, waarneming

B = ("25475", 3, "BOL")


def _scenario():
    pm = peilmomenten(
        [
            ("d1", 2022, *B),
            ("d2", 2022, *B),
            ("d3", 2022, *B),
            ("d4", 2022, *B),
            ("d4", 2023, *B),
            ("d5", 2022, *B),
            ("d6", 2022, "25250", 1, "BOL"),
            ("d7", 2022, *B),
            ("d7", 2023, "99000", 3, "OVO"),
        ]
    )
    dip = diplomas(
        [
            ("d1", "25498", 2, date(2019, 6, 30)),
            ("d2", "25498", 2, date(2017, 6, 30)),
            ("d5", "25475", 3, date(2023, 8, 15)),
            ("d6", "25250", 1, date(2020, 6, 30)),
        ]
    )
    return pm, dip


def _rij(uit, jaartijdvak, crebo):
    rijen = uit.filter(
        (uit["Jaartijdvak"] == jaartijdvak) & (uit["Opleidingcode"] == crebo)
    ).to_dicts()
    assert len(rijen) == 1
    return rijen[0]


def test_diplomaresultaat_teller_en_noemer_van_het_voorbeeld():
    pm, dip = _scenario()
    uit = diplomaresultaat(pm, dip, waarneming(2018, 2025))
    rij = _rij(uit, 2022, "25475")
    # Teller: d1 (eerder n2-diploma) en d5. Noemer: + d2 (diploma te oud) en d3.
    # d4 blijft, d6 zit in entree, d7 staat nog bij een eigen BRIN.
    assert (rij["Teller"], rij["Noemer"]) == (2, 4)


def test_diplomaresultaat_stapelaar_die_uitvalt_telt_positief():
    pm = peilmomenten([("s", 2022, *B)])
    dip = diplomas([("s", "25498", 2, date(2019, 6, 30))])
    rij = diplomaresultaat(pm, dip, waarneming(2018, 2025)).to_dicts()[0]
    assert (rij["Teller"], rij["Noemer"]) == (1, 1)
    assert rij["Niveau"] == 3  # toegerekend aan de opleiding waaruit hij vertrekt


def test_diplomaresultaat_diplomavenster_begint_op_1_oktober_vijf_jaar_eerder():
    pm = peilmomenten([("a", 2022, *B), ("b", 2022, *B)])
    dip = diplomas(
        [
            ("a", "25498", 2, date(2017, 10, 1)),
            ("b", "25498", 2, date(2017, 9, 30)),
        ]
    )
    rij = diplomaresultaat(pm, dip, waarneming(2014, 2025)).to_dicts()[0]
    assert (rij["Teller"], rij["Noemer"]) == (1, 2)


def test_diplomaresultaat_entreediploma_telt_niet():
    pm = peilmomenten([("s", 2022, *B)])
    dip = diplomas([("s", "25250", 1, date(2020, 6, 30))])
    rij = diplomaresultaat(pm, dip, waarneming(2018, 2025)).to_dicts()[0]
    assert (rij["Teller"], rij["Noemer"]) == (0, 1)


def test_diplomaresultaat_entreeverlater_valt_buiten_de_populatie():
    pm = peilmomenten([("e", 2022, "25250", 1, "BOL")])
    assert diplomaresultaat(pm, diplomas([]), waarneming(2018, 2025)).is_empty()


def test_diplomaresultaat_volledig_hangt_af_van_de_diplomahistorie():
    pm = peilmomenten([("s", 2022, *B)])
    dip = diplomas([])
    kort = diplomaresultaat(pm, dip, waarneming(2018, 2025))
    lang = diplomaresultaat(pm, dip, waarneming(2014, 2025))
    # Voor t = 2022 zijn de diploma's vanaf 1-10-2017 nodig.
    assert kort["Volledig"].to_list() == [False]
    assert lang["Volledig"].to_list() == [True]


def test_diplomaresultaat_laatste_jaartijdvak_en_gat_zijn_niet_waarneembaar():
    pm = peilmomenten([("s", t, *B) for t in (2021, 2022, 2025)])
    uit = diplomaresultaat(pm, diplomas([]), waarneming(2018, 2025, gaten=[2022]))
    assert uit["Jaartijdvak"].to_list() == []


def test_diplomaresultaat_heeft_het_afgesproken_schema():
    pm, dip = _scenario()
    uit = diplomaresultaat(pm, dip, waarneming(2018, 2025))
    assert uit.columns == [
        "Jaartijdvak",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "Teller",
        "Noemer",
        "Volledig",
    ]
