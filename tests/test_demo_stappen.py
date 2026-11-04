import importlib.util
import re
from pathlib import Path

import pytest

DEMO = Path(__file__).parent.parent / "demo-video"


@pytest.fixture(scope="module")
def stappen():
    spec = importlib.util.spec_from_file_location("stappen", DEMO / "stappen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.STAPPEN


def test_elke_stap_heeft_een_korte_ondertitel_en_een_uitspraak(stappen):
    assert stappen
    for naam, ondertitel, uitspraak in stappen:
        assert 0 < len(ondertitel) <= 110, naam
        assert uitspraak.strip(), naam


def test_stap_ids_zijn_uniek(stappen):
    namen = [naam for naam, _, _ in stappen]
    assert len(namen) == len(set(namen))


def test_scenes_per_pagina_en_de_stapeluitleg(stappen):
    namen = {naam for naam, _, _ in stappen}
    assert {"demodata", "gelukt", "studiesucces", "cohorten", "loopbanen", "over"} <= (
        namen
    )
    tekst = " ".join(ondertitel for _, ondertitel, _ in stappen)
    assert "Stapelen telt niet als uitval of wissel" in tekst
    assert "indicatief" in tekst.lower()


def test_opname_noemt_elke_stap_van_de_voice_over():
    record = (DEMO / "scenes" / "record.py").read_text(encoding="utf-8")
    spec = importlib.util.spec_from_file_location("stappen", DEMO / "stappen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for naam, _, _ in module.STAPPEN:
        assert re.search(rf'["\']{naam}["\']', record), naam
