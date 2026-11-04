import importlib.util
import random
from pathlib import Path

import polars as pl
import pytest

from staat_mbo.analyse import bereken

SCRIPT = Path(__file__).parent.parent / "scripts" / "maak_demodata.py"


@pytest.fixture(scope="module")
def script():
    spec = importlib.util.spec_from_file_location("maak_demodata", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def resultaten(demodata_analyse):
    return bereken(demodata_analyse)


def _aantal(df: pl.DataFrame, **filters) -> int:
    for kolom, waarde in filters.items():
        df = df.filter(pl.col(kolom) == waarde)
    return int(df["Aantal"].sum())


def test_tien_jaar_een_instelling_onder_de_tweeduizend_studenten(demodata_analyse):
    w = demodata_analyse.waarneming
    assert (w.eerste_jaar, w.laatste_jaar) == (2016, 2025)
    assert demodata_analyse.peilmomenten["BRIN"].n_unique() == 1
    assert demodata_analyse.peilmomenten["_persoon_id"].n_unique() < 2000


def test_stapelen_van_entree_naar_niveau_2(resultaten):
    na_diploma = resultaten.instroom.filter(pl.col("Herkomst") == "na diploma")
    assert _aantal(na_diploma, Niveau=2) >= 20


def test_stapelen_naar_niveau_3_en_4(resultaten):
    verder = resultaten.loopbanen.filter(
        (pl.col("Status") == "Diploma, verder op hoger niveau") & (pl.col("Jaren") == 3)
    )
    assert _aantal(verder, Niveau=2) >= 30
    assert _aantal(verder, Niveau=3) >= 15


def test_opstromen_en_afstromen_zonder_diploma(resultaten):
    na_een_jaar = resultaten.loopbanen.filter(pl.col("Jaren") == 1)
    assert _aantal(na_een_jaar, Status="Zonder diploma, hoger niveau") >= 15
    assert _aantal(na_een_jaar, Status="Zonder diploma, lager niveau") >= 15


def test_stapelaars_vallen_uit_na_een_eerder_diploma(script):
    studenten = script.maak_studenten(random.Random(2026))
    uitvallers = [
        s
        for s in studenten
        if any(
            vorige.diploma and volgende.reden == script.REDEN_UITVAL
            for vorige, volgende in zip(s.inschrijvingen, s.inschrijvingen[1:])
        )
    ]
    assert len(uitvallers) >= 10


def test_crebo_vernieuwingen_geven_een_opleiding(demodata_analyse, resultaten):
    codes = set(demodata_analyse.peilmomenten["Opleidingcode"])
    assert {"25498", "25960"} <= codes  # oud en nieuw crebo komen allebei voor
    assert demodata_analyse.opvolgers["25498"] == "25960"
    opleidingen = resultaten.studiesucces.filter(pl.col("Groep") == "opleiding")
    assert "25498" not in set(opleidingen["Opleidingcode"])
    assert "25960" in set(opleidingen["Opleidingcode"])


def test_elke_indicator_heeft_volledige_driejaarscijfers(resultaten):
    s = resultaten.studiesucces.filter(
        (pl.col("Groep") == "niveau") & pl.col("Volledig")
    )
    for indicator in ("JR", "DR", "SR"):
        for niveau in (2, 3, 4):
            rijen = s.filter(
                (pl.col("Indicator") == indicator) & (pl.col("Niveau") == niveau)
            )
            assert rijen.height >= 1, (indicator, niveau)


def test_per_niveau_een_opleiding_onder_en_boven_de_norm(resultaten):
    s = resultaten.studiesucces.filter(
        (pl.col("Groep") == "opleiding") & pl.col("Volledig") & ~pl.col("Te_klein")
    )
    laatste = s.filter(pl.col("Jaartijdvak") == s["Jaartijdvak"].max())
    for indicator in ("JR", "DR", "SR"):
        for niveau in (2, 3, 4):
            rijen = laatste.filter(
                (pl.col("Indicator") == indicator) & (pl.col("Niveau") == niveau)
            )
            assert rijen["Onder_norm"].any(), (indicator, niveau, "onder")
            assert not rijen["Onder_norm"].all(), (indicator, niveau, "boven")


def test_diploma_verder_op_hoger_niveau_komt_voor(resultaten):
    verder = resultaten.loopbanen.filter(
        pl.col("Status") == "Diploma, verder op hoger niveau"
    )
    assert _aantal(verder) > 0


def test_instellingscijfers_volledig_voor_jr_dr_sr(resultaten):
    s = resultaten.studiesucces.filter(
        (pl.col("Groep") == "instelling") & pl.col("Volledig")
    )
    assert set(s["Indicator"]) == {"JR", "DR", "SR"}


def test_twee_keer_draaien_geeft_dezelfde_bestanden(script, tmp_path, monkeypatch):
    uitkomst = []
    for naam in ("een", "twee"):
        monkeypatch.setattr(script, "DOEL", tmp_path / naam)
        script.main()
        uitkomst.append({p.name: p.read_bytes() for p in (tmp_path / naam).iterdir()})
    assert uitkomst[0] == uitkomst[1]
    assert len(uitkomst[0]) == 5
