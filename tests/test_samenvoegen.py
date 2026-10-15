import json
from pathlib import Path

from staat_mbo.cli import main
from staat_mbo.samenvoegen import BESTAND_1CHO, BESTAND_MELDINGEN, BESTAND_RAPPORT
from tests.conftest import RUW


def test_demo_samenvoegen(ingebouwde_sleutel, tmp_path):
    invoer = [str(p) for p in sorted(RUW.iterdir())]
    code = main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path)])
    assert code == 0
    csv = (tmp_path / BESTAND_1CHO).read_text(encoding="utf-8")
    assert csv.startswith("persoonsgebonden_nummer;")
    rapport = json.loads((tmp_path / BESTAND_RAPPORT).read_text(encoding="utf-8"))
    assert rapport["ok"] is True
    assert (
        (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8").startswith("Gelukt")
    )


def test_demodata_vult_het_dashboard(ingebouwde_sleutel, tmp_path):
    """Genoeg jaren en studenten voor rendement, uitval en wissel per cohort."""
    demodata = Path(__file__).parent.parent / "demodata"
    code = main(["samenvoegen", str(demodata), "--uitvoer", str(tmp_path)])
    assert code == 0
    rapport = json.loads((tmp_path / BESTAND_RAPPORT).read_text(encoding="utf-8"))
    assert len(rapport["schooljaren"]) >= 10
    assert rapport["aantal_studenten"] >= 3000


def test_fout_geeft_exitcode_en_melding(ingebouwde_sleutel, tmp_path):
    invoer = [str(p) for p in RUW.glob("TBGI_*")]
    code = main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path)])
    assert code == 1
    meldingen = (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8")
    assert meldingen.startswith("Niet gelukt") and "Geen RO" in meldingen
    assert not (tmp_path / BESTAND_1CHO).exists()


def test_kapot_bestand_geeft_melding_zonder_traceback(
    ingebouwde_sleutel, tmp_path, capsys
):
    kapot = tmp_path / "RO_99XX_20250101_20251231.csv"
    kapot.write_text("dit;is;geen;RO\n", encoding="utf-8")
    code = main(["samenvoegen", str(kapot), "--uitvoer", str(tmp_path / "uit")])
    assert code == 1
    meldingen = (tmp_path / "uit" / BESTAND_MELDINGEN).read_text(encoding="utf-8")
    assert meldingen.startswith("Niet gelukt") and "RO_99XX" in meldingen
