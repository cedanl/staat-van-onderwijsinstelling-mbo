import shutil
import zipfile

import pytest

from staat_mbo.bron import VEREISTE_TABELLEN, InvoerFout, laad_star
from tests.conftest import RUW


def test_ruwe_bestanden_worden_star(demo_star):
    star, _ = demo_star
    for tabel in VEREISTE_TABELLEN:
        assert tabel in star
    assert set(star["fact_inschrijving_schooljaar"]["BRIN"]) == {"21CY", "25LX", "27DV"}


def test_datamodel_map_als_invoer(demo_star, tmp_path):
    _, werkmap = demo_star
    star = laad_star([werkmap / "star" / "datamodel"], tmp_path)
    assert star["fact_inschrijving_schooljaar"].height > 0


def test_losse_parquetbestanden_als_invoer(demo_star, tmp_path):
    _, werkmap = demo_star
    bestanden = sorted((werkmap / "star" / "datamodel").glob("*.parquet"))
    star = laad_star(bestanden, tmp_path)
    assert star["fact_inschrijving_schooljaar"].height > 0


def test_zip_als_invoer(demo_star, tmp_path):
    _, werkmap = demo_star
    zip_pad = tmp_path / "datamodel.zip"
    with zipfile.ZipFile(zip_pad, "w") as z:
        for f in (werkmap / "star" / "datamodel").glob("*.parquet"):
            z.write(f, f"datamodel/{f.name}")
    star = laad_star([zip_pad], tmp_path / "werk")
    assert star["fact_inschrijving_schooljaar"].height > 0


def test_zonder_salt_duidelijke_fout(monkeypatch, tmp_path):
    monkeypatch.delenv("MBO_PSEUDONIMISERING_SALT", raising=False)
    with pytest.raises(InvoerFout, match="MBO_PSEUDONIMISERING_SALT"):
        laad_star(sorted(RUW.glob("RO_*")), tmp_path)


def test_alleen_tbgi_geeft_fout(salt, tmp_path):
    with pytest.raises(InvoerFout, match="Geen RO"):
        laad_star(sorted(RUW.glob("TBGI_*")), tmp_path)


def test_onbekend_bestand_geeft_fout(salt, tmp_path):
    onbekend = tmp_path / "notities.txt"
    onbekend.write_text("x")
    with pytest.raises(InvoerFout, match="notities.txt"):
        laad_star([onbekend], tmp_path / "werk")


def test_grondslag_geweigerd(salt, tmp_path):
    g = tmp_path / "GRONDSLAG_IP_MBO_27DV_20251119_2025.csv"
    shutil.copy(next(RUW.glob("RO_27DV*")), g)
    with pytest.raises(InvoerFout, match="GRONDSLAG"):
        laad_star([g], tmp_path / "werk")


def test_kapot_ro_bestand_geeft_fout(salt, tmp_path):
    kapot = tmp_path / "RO_99XX_20250101_20251231.csv"
    kapot.write_text("dit;is;geen;RO\n1;2;3;4\n", encoding="utf-8")
    with pytest.raises(InvoerFout, match="RO_99XX"):
        laad_star([kapot], tmp_path / "werk")


def test_kapotte_zip_geeft_fout(tmp_path):
    kapot = tmp_path / "datamodel.zip"
    kapot.write_bytes(b"geen zip")
    with pytest.raises(InvoerFout, match="datamodel.zip"):
        laad_star([kapot], tmp_path / "werk")
