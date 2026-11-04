import json
import shutil

import polars as pl

from staat_mbo.analyse import DEMODATA
from staat_mbo.cli import main
from staat_mbo.samenvoegen import (
    BESTAND_DIPLOMAS,
    BESTAND_MELDINGEN,
    BESTAND_PEILMOMENTEN,
    BESTAND_RAPPORT,
)
from tests.conftest import RUW

STAAT_KOLOMMEN = [
    "Indicator",
    "Jaartijdvak",
    "Periode",
    "Groep",
    "Opleidingcode",
    "Niveau",
    "Leertraject",
    "Teller",
    "Noemer",
    "Percentage",
    "Norm",
    "Onder_norm",
    "Te_klein",
    "Volledig",
]


def test_demo_samenvoegen(ingebouwde_sleutel, tmp_path):
    invoer = [str(p) for p in sorted(RUW.glob("*27DV*"))]
    code = main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path)])
    assert code == 0
    assert (tmp_path / BESTAND_PEILMOMENTEN).exists()
    assert (tmp_path / BESTAND_DIPLOMAS).exists()
    assert not (tmp_path / "1cho_mbo.csv").exists()
    rapport = json.loads((tmp_path / BESTAND_RAPPORT).read_text(encoding="utf-8"))
    assert rapport["ok"] is True
    assert (
        (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8").startswith("Gelukt")
    )


def test_demodata_vult_het_dashboard(ingebouwde_sleutel, tmp_path):
    """Genoeg jaren en studenten voor rendement, uitval en wissel per cohort."""
    code = main(["samenvoegen", str(DEMODATA), "--uitvoer", str(tmp_path)])
    assert code == 0
    rapport = json.loads((tmp_path / BESTAND_RAPPORT).read_text(encoding="utf-8"))
    assert len(rapport["schooljaren"]) >= 6
    assert 1000 <= rapport["aantal_studenten"] <= 2000
    pm = pl.read_parquet(tmp_path / BESTAND_PEILMOMENTEN)
    assert pm["Niveau"].null_count() == 0
    assert pm.select(["_persoon_id", "Jaar"]).is_duplicated().any() is False


def test_fout_geeft_exitcode_en_melding(ingebouwde_sleutel, tmp_path):
    invoer = [str(p) for p in RUW.glob("TBGI_*")]
    code = main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path)])
    assert code == 1
    meldingen = (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8")
    assert meldingen.startswith("Niet gelukt") and "Geen RO" in meldingen
    assert not (tmp_path / BESTAND_PEILMOMENTEN).exists()


def test_kapot_bestand_geeft_melding_zonder_traceback(ingebouwde_sleutel, tmp_path):
    kapot = tmp_path / "RO_99XX_20250101_20251231.csv"
    kapot.write_text("dit;is;geen;RO\n", encoding="utf-8")
    code = main(["samenvoegen", str(kapot), "--uitvoer", str(tmp_path / "uit")])
    assert code == 1
    meldingen = (tmp_path / "uit" / BESTAND_MELDINGEN).read_text(encoding="utf-8")
    assert meldingen.startswith("Niet gelukt") and "RO_99XX" in meldingen


def test_staat_schrijft_csvs_en_meldingen(ingebouwde_sleutel, tmp_path, monkeypatch):
    # Zonder R moet het ook werken: staat roept geen Rscript aan.
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    code = main(["staat", str(DEMODATA), "--uitvoer", str(tmp_path)])
    assert code == 0
    studiesucces = pl.read_csv(tmp_path / "studiesucces.csv")
    assert studiesucces.columns == STAAT_KOLOMMEN
    assert not studiesucces.is_empty()
    assert not pl.read_csv(tmp_path / "cohorten.csv").is_empty()
    assert not pl.read_csv(tmp_path / "loopbanen.csv").is_empty()
    assert (
        (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8").startswith("Gelukt")
    )
    assert not (tmp_path / BESTAND_PEILMOMENTEN).exists()


def test_staat_met_kapotte_invoer_geeft_exitcode_1(ingebouwde_sleutel, tmp_path):
    kapot = tmp_path / "RO_99XX_20250101_20251231.csv"
    kapot.write_text("dit;is;geen;RO\n", encoding="utf-8")
    uit = tmp_path / "uit"
    assert main(["staat", str(kapot), "--uitvoer", str(uit)]) == 1
    assert not (uit / "studiesucces.csv").exists()
    assert (uit / BESTAND_MELDINGEN).read_text(encoding="utf-8").startswith("Niet")
