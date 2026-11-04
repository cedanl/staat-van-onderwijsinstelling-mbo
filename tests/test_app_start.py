from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from staat_mbo.analyse import DEMODATA, Analyse
from staat_mbo.app import invoer
from staat_mbo.app.ui import OMGEVING_INVOER, SESSIE_ANALYSE
from staat_mbo.stapelcontrole import Stapelrapport

APP = Path(__file__).parent.parent / "src" / "staat_mbo" / "app"


def _app(pagina: str = "start.py") -> AppTest:
    return AppTest.from_file(str(APP / pagina), default_timeout=120)


def test_selectie_staat_in_de_werkmap_zonder_padontsnapping(tmp_path):
    doel = invoer.synchroniseer_selectie([("a/../RO_x.csv", b"1")], tmp_path)
    assert doel == tmp_path / "selectie"
    assert [p.name for p in doel.iterdir()] == ["RO_x.csv"]
    assert not (tmp_path / "RO_x.csv").exists()


def test_oud_bestand_dat_niet_meer_gekozen_is_verdwijnt(tmp_path):
    invoer.synchroniseer_selectie([("RO_a.csv", b"1"), ("RO_b.csv", b"2")], tmp_path)
    doel = invoer.synchroniseer_selectie([("RO_b.csv", b"2")], tmp_path)
    assert sorted(p.name for p in doel.iterdir()) == ["RO_b.csv"]


def test_demodata_geeft_gelukt_en_historiemeldingen(ingebouwde_sleutel):
    at = _app().run()
    assert not at.exception
    at.button[1].click().run()
    assert not at.exception
    assert "Gelukt" in at.success[0].value
    ## Tien jaar historie: geen waarschuwing meer over DR of SR.
    assert not any("Diplomaresultaat" in w.value for w in at.warning)
    assert not any("Startersresultaat" in w.value for w in at.warning)
    assert at.session_state[SESSIE_ANALYSE].ok


def test_samenvoegen_zonder_bestanden_waarschuwt(ingebouwde_sleutel):
    at = _app().run()
    at.button[0].click().run()
    assert [w.value for w in at.warning] == ["Kies eerst je bestanden."]


def test_mislukte_analyse_toont_de_fout_en_verbergt_de_pagina(ingebouwde_sleutel):
    kapot = Analyse(Stapelrapport([], [], [], 0, fouten=["RO_99XX: kapot"]))
    at = _app("studiesucces.py")
    at.session_state[SESSIE_ANALYSE] = kapot
    at.run()
    assert not at.exception
    assert "RO_99XX: kapot" in at.error[0].value
    assert any("Voeg eerst je bestanden samen" in i.value for i in at.info)


def test_zonder_analyse_vraagt_pagina_om_samenvoegen():
    at = _app("studiesucces.py").run()
    assert any("Voeg eerst je bestanden samen" in i.value for i in at.info)


def test_omgevingsinvoer_laadt_bij_de_start(ingebouwde_sleutel, monkeypatch):
    monkeypatch.setenv(OMGEVING_INVOER, str(DEMODATA))
    at = _app().run()
    assert not at.exception
    assert at.session_state[SESSIE_ANALYSE].ok
    assert "Gelukt" in at.success[0].value


@pytest.mark.parametrize("pagina", ["start.py", "main.py"])
def test_app_rendert_zonder_exception(ingebouwde_sleutel, pagina):
    assert not _app(pagina).run().exception


@pytest.mark.parametrize(
    "pagina",
    ["start.py", "studiesucces.py", "cohorten.py", "loopbanen.py", "over.py"],
)
def test_elke_pagina_rendert_op_de_demodata_zonder_exception(demodata_analyse, pagina):
    at = _app(pagina)
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    at.run()
    assert not at.exception


def test_start_toont_zes_kerncijfertegels_op_de_demodata(demodata_analyse):
    at = _app()
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    at.run()
    assert not at.exception
    assert [m.value for m in at.metric] == [
        "67,9%",
        "68,9%",
        "80,7%",
        "226",
        "16,4%",
        "1,3%",
    ]
    assert any("Indicatief" in i.value for i in at.info)


def test_start_zonder_analyse_toont_geen_kerncijfers():
    assert not _app().run().metric
