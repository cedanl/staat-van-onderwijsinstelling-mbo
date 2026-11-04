import polars as pl

from staat_mbo.analyse import bereken, maak_analyse
from tests.conftest import RUW


def test_analyse_op_de_fixtures(ingebouwde_sleutel, tmp_path):
    analyse = maak_analyse(sorted(RUW.iterdir()), tmp_path)
    assert analyse.ok and analyse.rapport.ok
    assert not analyse.peilmomenten.is_empty()
    assert not analyse.diplomas.is_empty()
    assert analyse.regels()[0].startswith("Gelukt")
    # De fixtures zijn bewust een mengsel van BRIN's zonder gedeelde 1 oktober:
    # er is dan geen waarneembaar jaar, en de berekening geeft lege tabellen.
    assert bereken(analyse).studiesucces.is_empty()


def test_demodata_heeft_waarneembare_jaren(demodata_analyse):
    w = demodata_analyse.waarneming
    assert w.eerste_jaar <= w.laatste_jaar


def test_kapot_bestand_geeft_fouttekst(ingebouwde_sleutel, tmp_path):
    kapot = tmp_path / "RO_99XX_20250101_20251231.csv"
    kapot.write_text("dit;is;geen;RO\n", encoding="utf-8")
    analyse = maak_analyse([kapot], tmp_path / "werk")
    assert analyse.rapport.ok is False
    assert "RO_99XX" in analyse.rapport.fouten[0]
    assert analyse.peilmomenten is None
    assert analyse.regels()[0] == "Niet gelukt."


def test_regels_bevatten_historiemeldingen(ingebouwde_sleutel, tmp_path):
    analyse = maak_analyse(sorted(RUW.iterdir()), tmp_path)
    tekst = "\n".join(analyse.regels())
    assert "Rendement nominaal + 1" in tekst


def test_bereken_op_de_demodata(demodata_analyse):
    r = bereken(demodata_analyse)
    s = r.studiesucces
    assert set(s["Indicator"]) == {"JR", "DR", "SR"}
    assert set(s["Groep"]) == {"instelling", "niveau", "opleiding", "opleiding_leerweg"}
    klein = s.filter(pl.col("Te_klein"))
    assert klein["Percentage"].null_count() == klein.height
    assert not r.instroom.is_empty()
    assert {"Instroom_nieuw", "Instroom_na diploma", "Uitval_1_percentage"} <= set(
        r.cohorten.columns
    )
    assert set(r.loopbanen["Jaren"]) == {1, 2, 3}
    assert {"weg", "n2", "n3"} <= set(r.overgangen["Naar"])
    # De herkomst telt op tot de instroom.
    herkomst = r.cohorten.select(pl.sum_horizontal(pl.col("^Instroom_.*$")))
    assert herkomst.to_series().sum() == r.cohorten["Instroom"].sum()


def test_uitval_en_status_hebben_een_rij_per_cohortrij(demodata_analyse):
    r = bereken(demodata_analyse)
    per_k = r.loopbanen.group_by("Jaren").agg(pl.col("Aantal").sum())
    assert per_k["Aantal"].n_unique() == 1
    assert per_k["Aantal"][0] == r.instroom["Aantal"].sum()


def test_kerncijfers_zijn_tellingen_over_de_bestanden(demodata_analyse):
    from staat_mbo.analyse import kerncijfers

    tegels = {t.naam: t for t in kerncijfers(demodata_analyse)}
    assert list(tegels) == [
        "Studenten",
        "Schooljaren",
        "Ingeschreven op 1 oktober 2025",
        "Diploma's",
        "Opleidingen",
        "BRIN-nummers",
    ]
    assert tegels["Studenten"].waarde == "1.743"
    assert tegels["Schooljaren"].waarde == "10"
    assert tegels["Schooljaren"].ondertitel == "1 oktober 2016 t/m 2025"
    assert tegels["Ingeschreven op 1 oktober 2025"].waarde == "564"
    assert tegels["Diploma's"].waarde == "953"
    assert tegels["Opleidingen"].waarde == "11"
    assert tegels["BRIN-nummers"].ondertitel == "27DV"
    assert all(t.help for t in tegels.values())


def test_kerncijfers_van_een_korte_reeks(kort_analyse):
    from staat_mbo.analyse import kerncijfers

    tegels = {t.naam: t for t in kerncijfers(kort_analyse)}
    assert tegels["Schooljaren"].getal == 6
