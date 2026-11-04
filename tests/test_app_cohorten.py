from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from staat_mbo.app.ui import SESSIE_ANALYSE
from staat_mbo.cohorten import HERKOMSTEN

PAGINA = Path(__file__).parent.parent / "src/staat_mbo/app/cohorten.py"


@pytest.fixture
def pagina(demodata_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    return at.run()


def _grafieken(at) -> list[str]:
    return [g.proto.spec for g in at.get("vega_lite_chart")]


def test_instroomgrafiek_heeft_de_herkomstcategorieen(pagina):
    assert not pagina.exception
    instroom = _grafieken(pagina)[0]
    for herkomst in HERKOMSTEN:
        assert herkomst in instroom


def test_er_zijn_drie_grafieken_en_het_label(pagina):
    assert len(_grafieken(pagina)) == 3
    assert any("Indicatief" in i.value for i in pagina.info)


def test_rendementstabel_heeft_de_verwachte_kolommen(pagina):
    tabel = pagina.dataframe[0].value
    verwacht = [
        "Cohort",
        "Opleiding",
        "Duur",
        "Duur uit",
        "Nominaal %",
        "Nominaal + 1 %",
        "Nog niet waarneembaar",
    ]
    assert set(verwacht) <= set(tabel.columns)
    assert set(tabel["Duur uit"]) <= {"geplande einddatum", "standaardduur"}


def test_recent_cohort_toont_nog_niet_waarneembaar_in_plaats_van_nul(pagina):
    tabel = pagina.dataframe[0].value
    recent = tabel[tabel["Cohort"] == tabel["Cohort"].max()]
    assert (recent["Nominaal %"] == "nog niet waarneembaar").all()
    assert not recent["Nominaal %"].str.contains("0,0%").any()
    assert (recent["Nog niet waarneembaar"] > 0).all()
    # Het oudste cohort is wel te zien.
    oud = tabel[tabel["Cohort"] == tabel["Cohort"].min()]
    assert oud["Nominaal %"].str.endswith("%").all()
    assert not (oud["Nominaal %"] == "nog niet waarneembaar").any()


def test_uitval_na_een_jaar_is_aanwezig(pagina):
    tabel = pagina.dataframe[0].value
    assert "Uitval na 1 jaar %" in tabel.columns
    assert tabel["Uitval na 1 jaar %"].str.endswith("%").any()


def test_filter_op_oud_crebo_selecteert_het_nieuwe_crebo(pagina):
    # 25132 (accountmanager) is in de demodata vervangen door 25877.
    pagina.multiselect(key="filter_opleiding").set_value(["25132"]).run()
    assert not pagina.exception
    tabel = pagina.dataframe[0].value
    assert len(tabel) > 0
    assert tabel["Opleiding"].str.contains("25877").all()


def test_filter_niveau_beperkt_de_tabel(pagina):
    pagina.multiselect(key="filter_niveau").set_value([2]).run()
    assert set(pagina.dataframe[0].value["Niveau"]) == {2}
