from pathlib import Path

import polars as pl
import pytest
from streamlit.testing.v1 import AppTest

from staat_mbo.analyse import dekking
from staat_mbo.app.ui import SESSIE_ANALYSE
from staat_mbo.cohorten import CATEGORIEEN
from staat_mbo.definities import CATEGORIE_KLEUREN, CATEGORIE_TOELICHTING, DEFINITIES
from tests.maak import waarneming

PAGINA = Path(__file__).parent.parent / "src/staat_mbo/app/over.py"
INDICATOREN = [
    "jr",
    "dr",
    "sr",
    "driejaarscijfer",
    "instroomcohort",
    "rendement_nominaal",
    "rendement_nominaal_plus_1",
    "uitval",
    "loopbaanstatus",
    "studiewissel",
]


@pytest.fixture
def pagina(demodata_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    return at.run()


def test_elke_indicator_heeft_een_definitie():
    for sleutel in INDICATOREN:
        assert DEFINITIES[sleutel].strip()


def test_elke_loopbaancategorie_heeft_uitleg_en_kleur():
    assert list(CATEGORIE_TOELICHTING) == CATEGORIEEN
    assert len(set(CATEGORIE_KLEUREN)) == len(CATEGORIEEN)


def test_pagina_noemt_definities_en_bronlinks(pagina):
    assert not pagina.exception
    tekst = " ".join(m.value for m in pagina.markdown)
    assert "stcrt-2022-18467" in tekst and "stb-2022-273" in tekst
    for sleutel in INDICATOREN:
        assert DEFINITIES[sleutel] in tekst
    assert any("Indicatief" in i.value for i in pagina.info)


def test_dekkingstabel_heeft_ja_onvolledig_en_nee(pagina):
    tabel = next(d.value for d in pagina.dataframe if "Indicator" in d.value)
    assert list(tabel["Indicator"]) == ["JR", "DR", "SR"]
    waarden = set(tabel.drop(columns="Indicator").to_numpy().ravel())
    assert waarden == {"ja", "onvolledig", "nee"}


def test_dekking_met_genoeg_en_te_weinig_historie():
    sr = dekking(waarneming(2014, 2025)).filter(pl.col("Indicator") == "SR")
    rij = sr.row(0, named=True)
    assert rij["2022-2023"] == "ja"
    assert rij["2025-2026"] == "nee"  # 1 oktober 2026 valt buiten de bestanden
    assert rij["2014-2015"] == "nee"  # geen terugblik mogelijk
    dr = dekking(waarneming(2020, 2025)).filter(pl.col("Indicator") == "DR")
    assert dr.row(0, named=True)["2022-2023"] == "onvolledig"


def test_meldingen_staan_op_de_pagina(kort_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = kort_analyse
    at.run()
    tekst = " ".join(m.value for m in at.markdown)
    assert "Diplomaresultaat: diploma's van vóór" in tekst
