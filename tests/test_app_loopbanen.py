from pathlib import Path

import polars as pl
import pytest
from streamlit.testing.v1 import AppTest

from staat_mbo.analyse import MOMENTEN
from staat_mbo.app.ui import SESSIE_ANALYSE
from staat_mbo.cohorten import CATEGORIEEN
from staat_mbo.definities import CATEGORIE_KLEUREN as KLEUREN

PAGINA = Path(__file__).parent.parent / "src/staat_mbo/app/loopbanen.py"


@pytest.fixture
def pagina(demodata_analyse):
    at = AppTest.from_file(str(PAGINA), default_timeout=120)
    at.session_state[SESSIE_ANALYSE] = demodata_analyse
    return at.run()


def _tabellen(at):
    return {d.value.columns[0]: d.value for d in at.dataframe}


@pytest.mark.parametrize("moment", MOMENTEN)
def test_verdeling_telt_per_rij_op_tot_100_procent(pagina, moment):
    pagina.radio[0].set_value(moment).run()
    assert not pagina.exception
    tabel = pagina.dataframe[0].value
    assert (tabel["Totaal"] == 100).all()
    totalen = tabel[CATEGORIEEN].sum(axis=1)
    assert ((totalen - 100).abs() < 0.5).all()
    assert (tabel["n"] > 0).all()


def test_overgangsmatrix_heeft_alle_niveaus_en_weg(pagina):
    matrix = pagina.dataframe[1].value
    assert list(matrix.columns) == ["Van", "n1", "n2", "n3", "n4", "weg"]
    assert list(matrix["Van"]) == ["n1", "n2", "n3", "n4"]


def test_categorieen_hebben_een_vaste_volgorde_en_kleur(pagina):
    tabel = pagina.dataframe[0].value
    assert [c for c in tabel.columns if c in CATEGORIEEN] == CATEGORIEEN
    assert len(set(KLEUREN)) == len(CATEGORIEEN)
    spec = pagina.get("vega_lite_chart")[0].proto.spec
    for kleur in KLEUREN:
        assert kleur in spec


def test_bij_studiewissel_staat_de_uitleg(pagina):
    assert not any("Stapelen telt niet als wissel" in c.value for c in pagina.caption)
    pagina.selectbox[0].set_value("Studiewissel").run()
    assert any("Stapelen telt niet als wissel" in c.value for c in pagina.caption)


def test_matrix_zonder_diploma_en_percentage(pagina):
    pagina.radio[3].set_value("% van de rij").run()
    matrix = pagina.dataframe[1].value
    rij = matrix[matrix["Van"] == "n2"].iloc[0]
    assert abs(rij[["n1", "n2", "n3", "n4", "weg"]].sum() - 100) < 0.5


def test_label_en_geen_exception(pagina):
    assert not pagina.exception
    assert any("Indicatief" in i.value for i in pagina.info)


def test_na_nominale_duur_hebben_alle_niveaus_diplomas(demodata_analyse):
    """Na een vast jaar heeft alleen entree een diploma; na de duur elk niveau."""
    from staat_mbo.analyse import bereken

    l = bereken(demodata_analyse).loopbanen.filter(
        (pl.col("Moment") == "na nominale duur")
        & pl.col("Status").is_in(CATEGORIEEN[:3])
    )
    per_niveau = l.group_by("Niveau").agg(pl.col("Aantal").sum())
    assert set(per_niveau["Niveau"]) == {1, 2, 3, 4}
    assert (per_niveau["Aantal"] > 20).all()


def test_standaard_staat_het_moment_op_nominale_duur(pagina):
    assert pagina.radio[0].value == "na nominale duur"
