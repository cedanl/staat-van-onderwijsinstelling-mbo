import json

from staat_mbo.cli import main
from staat_mbo.samenvoegen import BESTAND_1CHO, BESTAND_MELDINGEN, BESTAND_RAPPORT
from tests.conftest import RUW


def test_demo_samenvoegen(salt, tmp_path):
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


def test_fout_geeft_exitcode_en_melding(salt, tmp_path):
    invoer = [str(p) for p in RUW.glob("TBGI_*")]
    code = main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path)])
    assert code == 1
    meldingen = (tmp_path / BESTAND_MELDINGEN).read_text(encoding="utf-8")
    assert meldingen.startswith("Niet gelukt") and "Geen RO" in meldingen
    assert not (tmp_path / BESTAND_1CHO).exists()
