from pathlib import Path

import pytest

## Kleine nep-DUO-bestanden in verschillende varianten (geen echte studenten).
## De grote set voor gebruikers staat in src/staat_mbo/demodata/ (scripts/maak_demodata.py).
RUW = Path(__file__).parent / "fixtures" / "ruw"


@pytest.fixture
def ingebouwde_sleutel(monkeypatch):
    """Geen eigen sleutel gezet: de ingebouwde sleutel wordt gebruikt."""
    monkeypatch.delenv("MBO_PSEUDONIMISERING_SALT", raising=False)


@pytest.fixture(scope="session")
def demo_star(tmp_path_factory):
    """Star van de demodata, één keer per testsessie gebouwd."""
    from staat_mbo.bron import laad_star

    werkmap = tmp_path_factory.mktemp("demo")
    return laad_star(sorted(RUW.iterdir()), werkmap), werkmap


@pytest.fixture(scope="session")
def demodata_star(tmp_path_factory):
    """Star van de demodata (één instelling, meerdere jaren), één keer gebouwd."""
    from staat_mbo.analyse import DEMODATA as demodata
    from staat_mbo.bron import laad_star

    return laad_star([demodata], tmp_path_factory.mktemp("demodata"))


@pytest.fixture(scope="session")
def kort_analyse(tmp_path_factory):
    """Analyse van de eerste zes schooljaren van de demodata (DR en SR nog onvolledig)."""
    import shutil

    from staat_mbo.analyse import DEMODATA as demodata
    from staat_mbo.analyse import maak_analyse

    invoer = tmp_path_factory.mktemp("kort")
    for pad in sorted(demodata.glob("RO_*.csv"))[:3]:
        shutil.copy(pad, invoer / pad.name)
    return maak_analyse([invoer], tmp_path_factory.mktemp("kort_analyse"))


@pytest.fixture(scope="session")
def demodata_analyse(tmp_path_factory):
    """Analyse van de demodata, één keer per testsessie gebouwd."""
    from staat_mbo.analyse import DEMODATA as demodata
    from staat_mbo.analyse import maak_analyse

    return maak_analyse([demodata], tmp_path_factory.mktemp("analyse"))
