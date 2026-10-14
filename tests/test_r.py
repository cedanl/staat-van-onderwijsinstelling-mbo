import shutil
import subprocess

import pytest

from staat_mbo.cli import main
from staat_mbo.r import RFout, controleer_staat1cho, r_env, script_pad, vind_rscript
from tests.conftest import RUW


def _heeft_r() -> bool:
    try:
        vind_rscript()
    except RFout:
        return False
    return True


heeft_r = _heeft_r()


def test_geen_r_duidelijke_fout(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _: None)
    monkeypatch.setattr("staat_mbo.r._WINDOWS_R", "Z:/bestaat-niet/R")
    with pytest.raises(RFout, match="R is niet gevonden"):
        vind_rscript()


@pytest.mark.skipif(not heeft_r, reason="R niet geïnstalleerd")
def test_staat_op_demodata(salt, tmp_path):
    invoer = [str(p) for p in sorted(RUW.iterdir())]
    assert main(["samenvoegen", *invoer, "--uitvoer", str(tmp_path / "s")]) == 0
    csv = str(tmp_path / "s" / "1cho_mbo.csv")
    assert main(["staat", csv, "--uitvoer", str(tmp_path / "o")]) == 0
    assert list((tmp_path / "o").rglob("Benchmarkrapport_*.xlsx"))
    assert list((tmp_path / "o").rglob("Indicatoren_1cHO_*.RDS"))


@pytest.mark.skipif(not heeft_r, reason="R niet geïnstalleerd")
def test_voorstap_kopieert_met_originele_naam(salt, tmp_path):
    """Shiny noemt uploads 0.csv, 1.csv; het bestandstype hangt af van de naam."""
    rscript = vind_rscript()
    controleer_staat1cho(rscript)
    hernoemd = []
    for i, bron in enumerate(sorted(RUW.iterdir())):
        doel = tmp_path / f"{i}{bron.suffix}"
        shutil.copy(bron, doel)
        hernoemd.append((bron.name, doel.as_posix()))
    namen = ",".join(f'"{n}"' for n, _ in hernoemd)
    paden = ",".join(f'"{p}"' for _, p in hernoemd)
    code = (
        'source(Sys.getenv("STAAT_MBO_DASHBOARD_R"));'
        f"r <- smbo_samenvoegen(data.frame(name=c({namen}), datapath=c({paden})));"
        'cat(r$ok, r$meldingen[1], sep="|")'
    )
    uit = subprocess.run(
        [str(rscript), "-e", code],
        check=False,
        env={
            **r_env(),
            "STAAT_MBO_DASHBOARD_R": script_pad("dashboard.R").as_posix(),
            "STAAT_MBO_ALLEEN_FUNCTIES": "1",
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert uit.stdout.startswith("TRUE|Gelukt"), uit.stderr
