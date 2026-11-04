from datetime import date

from staat_mbo.indicatoren import startersresultaat
from tests.maak import diplomas, peilmomenten, waarneming

A = ("25498", 2, "BOL")
B = ("25475", 3, "BOL")


def _scenario():
    pm = peilmomenten(
        [
            ("n1", 2022, *A),
            ("n1", 2023, *A),
            ("n2", 2022, *A),
            ("n3", 2022, *A),
            ("n4", 2017, *A),
            ("n4", 2022, *A),
            ("n5", 2015, *A),
            ("n5", 2022, *A),
            ("n6", 2022, *A),
            ("n6", 2023, "25250", 1, "BOL"),
            ("n7", 2022, *A),
            ("n7", 2023, *B),
        ]
    )
    dip = diplomas([("n2", "25498", 2, date(2023, 7, 1))])
    return pm, dip


def _rij(uit, t, crebo="25498"):
    rijen = uit.filter(
        (uit["Jaartijdvak"] == t) & (uit["Opleidingcode"] == crebo)
    ).to_dicts()
    assert len(rijen) == 1
    return rijen[0]


def test_startersresultaat_teller_noemer_en_terugblik_van_het_voorbeeld():
    pm, dip = _scenario()
    rij = _rij(startersresultaat(pm, dip, waarneming(2014, 2025)), 2022)
    # Nieuw: n1, n2, n3, n5, n6, n7 (n4 stond in 2017). Positief: n1 (blijft),
    # n2 (diploma), n7 (opgestroomd). n3 weg, n6 afgestroomd naar entree.
    assert (rij["Teller"], rij["Noemer"], rij["Terugblik"]) == (3, 6, 6)


def test_startersresultaat_zes_jaar_terug_telt_mee_zeven_jaar_niet():
    pm = peilmomenten(
        [("a", 2016, *A), ("a", 2022, *A), ("b", 2015, *A), ("b", 2022, *A)]
    )
    rij = _rij(startersresultaat(pm, diplomas([]), waarneming(2014, 2025)), 2022)
    assert rij["Noemer"] == 1  # alleen b is nieuw; a stond 6 jaar eerder


def test_startersresultaat_verkorte_terugblik_bij_te_weinig_historie():
    pm, dip = _scenario()
    uit = startersresultaat(pm, dip, waarneming(2020, 2025))
    rij = _rij(uit, 2022)
    assert rij["Terugblik"] == 2
    # n4 (2017) en n5 (2015) zijn buiten beeld en tellen nu als nieuw.
    assert rij["Noemer"] == 7


def test_startersresultaat_eerste_jaar_heeft_geen_terugblik():
    pm, dip = _scenario()
    uit = startersresultaat(pm, dip, waarneming(2022, 2025))
    assert 2022 not in uit["Jaartijdvak"].to_list()


def test_startersresultaat_afstromen_naar_entree_is_niet_positief():
    pm = peilmomenten([("s", 2022, *A), ("s", 2023, "25250", 1, "BOL")])
    rij = _rij(startersresultaat(pm, diplomas([]), waarneming(2014, 2025)), 2022)
    assert (rij["Teller"], rij["Noemer"]) == (0, 1)


def test_startersresultaat_wisselen_binnen_de_instelling_is_positief():
    pm = peilmomenten([("s", 2022, *A), ("s", 2023, "25225", 2, "BOL")])
    rij = _rij(startersresultaat(pm, diplomas([]), waarneming(2014, 2025)), 2022)
    assert (rij["Teller"], rij["Noemer"]) == (1, 1)


def test_startersresultaat_starter_in_entree_staat_niet_in_de_uitvoer():
    pm = peilmomenten([("e", 2022, "25250", 1, "BOL")])
    assert startersresultaat(pm, diplomas([]), waarneming(2014, 2025)).is_empty()


def test_startersresultaat_gat_en_laatste_jaar_zijn_niet_waarneembaar():
    pm = peilmomenten([(f"s{t}", t, *A) for t in (2019, 2020, 2021, 2022, 2025)])
    uit = startersresultaat(pm, diplomas([]), waarneming(2014, 2025, gaten=[2021]))
    # t = 2020 kijkt naar 2021 vooruit, t = 2022 naar 2021 terug, 2025 heeft
    # geen t+1. Alleen 2019 blijft over.
    assert uit["Jaartijdvak"].to_list() == [2019]


def test_startersresultaat_heeft_het_afgesproken_schema():
    pm, dip = _scenario()
    uit = startersresultaat(pm, dip, waarneming(2014, 2025))
    assert uit.columns == [
        "Jaartijdvak",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "Teller",
        "Noemer",
        "Terugblik",
    ]
