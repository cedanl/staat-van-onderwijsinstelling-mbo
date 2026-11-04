import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from staat_mbo.app.ui import SESSIE_ANALYSE

PAGINA = Path(__file__).parent.parent / "src/staat_mbo/app/studiesucces.py"


@pytest.fixture
def pagina(demodata_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    return at.run()


def _tekst(at) -> str:
    """Alle zichtbare tekst van de pagina, voor de guard tegen een oordeel."""
    delen = [e.value for e in (*at.markdown, *at.info, *at.caption, *at.warning)]
    delen += [m.label + " " + m.value for m in at.metric]
    delen += [str(v) for df in at.dataframe for v in df.value.to_numpy().ravel()]
    return " ".join(delen)


def test_drie_tegels_met_de_indicatoren(pagina):
    assert not pagina.exception
    assert [m.label for m in pagina.metric] == [
        "Jaarresultaat",
        "Diplomaresultaat",
        "Startersresultaat",
    ]
    assert all("%" in m.value for m in pagina.metric)


def test_tabel_heeft_de_verwachte_kolommen(pagina):
    tabel = pagina.dataframe[0].value
    assert list(tabel.columns) == [
        "Opleiding",
        "Niveau",
        "Leerweg",
        "JR",
        "DR",
        "SR",
        "n",
        "Norm",
    ]
    assert len(tabel) > 5


def test_te_kleine_rij_toont_geen_getal(pagina):
    tabel = pagina.dataframe[0].value
    klein = [c for c in tabel["JR"] if "te weinig studenten" in c]
    assert klein, "de demodata heeft opleidingen met een noemer onder 12"
    assert all(re.fullmatch(r"te weinig studenten \(n = \d+\)", c) for c in klein)
    assert not any(re.search(r"\d%", c) for c in klein)


def test_label_en_geen_oordeel(pagina):
    tekst = _tekst(pagina)
    assert "Indicatief" in tekst
    schoon = tekst.replace("Geen oordeel", "").replace("Geen inspectieoordeel", "")
    for woord in ("oordeel", "voldoende studiesucces", "onder norm", "onvoldoende"):
        assert woord not in schoon.lower()
    assert "norm Regeling studiesucces mbo" in tekst


def test_filter_niveau_3_laat_alleen_niveau_3_zien(pagina):
    pagina.multiselect(key="filter_niveau").set_value([3]).run()
    assert not pagina.exception
    assert set(pagina.dataframe[0].value["Niveau"]) == {3}
    # Met één niveau krijgen de tegels de norm van dat niveau.
    assert any("norm Regeling studiesucces mbo: 68%" in c.value for c in pagina.caption)


def test_volledige_demodata_markeert_geen_onvolledig_cijfer(pagina):
    tabel = pagina.dataframe[0].value
    assert not any("⚠" in c for c in tabel["DR"])
    assert not any("onvolledig: zie" in c.value for c in pagina.caption)


def test_onvolledig_dr_cijfer_wordt_gemarkeerd(kort_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = kort_analyse
    pagina = at.run()
    tabel = pagina.dataframe[0].value
    assert any("⚠" in c for c in tabel["DR"])
    assert any("onvolledig" in c.value for c in pagina.caption)


def test_groeperen_per_niveau_geeft_een_rij_per_niveau(pagina):
    pagina.radio[0].set_value("Niveau").run()
    assert list(pagina.dataframe[0].value["Niveau"]) == [2, 3, 4]
