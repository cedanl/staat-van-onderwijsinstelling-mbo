import tomllib
from pathlib import Path

from streamlit.testing.v1 import AppTest

from staat_mbo import palet
from staat_mbo.app import huisstijl

ROOT = Path(__file__).parent.parent
APP = ROOT / "src" / "staat_mbo" / "app"
## Toegestane achtergrond/voorgrond-paren (design-tokens.json, allowed_combinations).
TOEGESTAAN = {
    palet.BLAUW: {palet.GEEL, palet.ROZE},
    palet.ROZE: {palet.BLAUW, palet.GROEN, palet.ZWART, palet.ORANJE},
}


def test_main_zet_de_huisstijl_css_op_de_pagina(ingebouwde_sleutel):
    at = AppTest.from_file(str(APP / "main.py"), default_timeout=120).run()
    assert not at.exception
    assert any("Plus Jakarta Sans" in m.value for m in at.markdown)
    assert any(palet.BLAUW in m.value for m in at.markdown)


def test_css_en_logo_zijn_package_data():
    assert huisstijl.CSS.is_file() and huisstijl.LOGO.is_file()
    assert "Inter" not in huisstijl.CSS.read_text(encoding="utf-8")


def test_thema_gaat_als_opties_mee_en_config_is_gelijk():
    opties = palet.thema_opties()
    assert opties[:2] == ["--theme.base", "light"]
    assert ["--theme.primaryColor", palet.BLAUW] == opties[2:4]
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text("utf-8"))
    thema = {k: v for k, v in config["theme"].items() if k != "sidebar"}
    thema |= {f"sidebar.{k}": v for k, v in config["theme"]["sidebar"].items()}
    assert thema == palet.THEMA


def test_zijbalk_is_roze_met_toegestane_tekst_en_zwart_is_nooit_achtergrond():
    thema = palet.THEMA
    assert thema["sidebar.backgroundColor"] == palet.ROZE
    assert thema["sidebar.textColor"] in TOEGESTAAN[palet.ROZE]
    achtergronden = [v for k, v in thema.items() if k.endswith("ackgroundColor")]
    assert palet.ZWART not in achtergronden


def test_grafiekthema_is_wit_met_het_gekozen_font():
    import altair as alt

    spec = huisstijl.stijl(alt.Chart({"values": [{"x": 1}]}).mark_bar()).to_dict()
    assert spec["config"]["background"] == palet.WIT
    assert "Plus Jakarta Sans" in spec["config"]["font"]
    assert "Inter" not in str(spec)
