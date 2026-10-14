from pathlib import Path

import pytest

## Demodata (nep, geen echte studenten) staat in de repo-root, ook voor gebruikers.
RUW = Path(__file__).parent.parent / "demodata"


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
