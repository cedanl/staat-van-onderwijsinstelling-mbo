import polars as pl

from staat_mbo.analyse import MOMENTEN, bereken, maak_analyse
from tests.conftest import RUW


def test_fixtures_zonder_gedeelde_1_oktober_zijn_niet_gelukt(
    ingebouwde_sleutel, tmp_path
):
    # De fixtures zijn bewust een mengsel van BRIN's zonder gedeelde 1 oktober:
    # dan valt er niets te berekenen, en dat zeggen we meteen.
    analyse = maak_analyse(sorted(RUW.iterdir()), tmp_path)
    assert not analyse.ok
    assert analyse.regels()[0] == "Niet gelukt."
    assert "geen 1 oktober gemeen" in analyse.regels()[1]


def test_een_echte_ro_met_oude_inschrijvingen(ingebouwde_sleutel, tmp_path):
    """Een RO noemt ook inschrijvingen van vóór zijn periode; die jaren tellen niet."""
    from staat_mbo.analyse import kerncijfers

    analyse = maak_analyse(sorted(RUW.glob("RO_27DV*")), tmp_path)
    assert analyse.ok
    assert not analyse.peilmomenten.is_empty()
    assert not analyse.diplomas.is_empty()
    tegels = {t.naam: t for t in kerncijfers(analyse)}
    ## De samenvatting na "Gelukt" en de tegel noemen hetzelfde aantal jaren.
    regel = next(r for r in analyse.regels() if r.startswith("Schooljaren"))
    assert regel.endswith(f"({tegels['Schooljaren'].waarde} jaar)")
    assert regel.startswith("Schooljaren: 2024")


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
    analyse = maak_analyse(sorted(RUW.glob("RO_27DV*")), tmp_path)
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
    assert set(r.loopbanen["Moment"]) == set(MOMENTEN)
    assert {"weg", "n2", "n3"} <= set(r.overgangen["Naar"])
    # De herkomst telt op tot de instroom.
    herkomst = r.cohorten.select(pl.sum_horizontal(pl.col("^Instroom_.*$")))
    assert herkomst.to_series().sum() == r.cohorten["Instroom"].sum()


def test_uitval_en_status_hebben_een_rij_per_cohortrij(demodata_analyse):
    r = bereken(demodata_analyse)
    per_k = r.loopbanen.group_by("Moment").agg(pl.col("Aantal").sum())
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
    assert tegels["Schooljaren"].waarde == "6"


def test_loopbanen_noemen_het_aantal_jaren_per_moment(demodata_analyse):
    lb = bereken(demodata_analyse).loopbanen
    assert set(lb.filter(pl.col("Moment") == "na 1 jaar")["Jaren"]) == {1}
    duur = lb.filter(pl.col("Moment") == "na nominale duur")
    plus = lb.filter(pl.col("Moment") == "na nominale duur + 1")
    assert set(duur["Jaren"]) <= {1, 2, 3, 4}
    assert min(plus["Jaren"]) == min(duur["Jaren"]) + 1
