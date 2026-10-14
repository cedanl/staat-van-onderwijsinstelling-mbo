from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
RUW = FIXTURES / "ruw"


@pytest.fixture
def salt(monkeypatch):
    monkeypatch.setenv("MBO_PSEUDONIMISERING_SALT", "test-salt-niet-geheim")


@pytest.fixture(scope="session")
def demo_star(tmp_path_factory):
    """Star van de demodata, één keer per testsessie gebouwd."""
    import os

    from staat_mbo.bron import laad_star

    os.environ.setdefault("MBO_PSEUDONIMISERING_SALT", "test-salt-niet-geheim")
    werkmap = tmp_path_factory.mktemp("demo")
    return laad_star(sorted(RUW.iterdir()), werkmap), werkmap
