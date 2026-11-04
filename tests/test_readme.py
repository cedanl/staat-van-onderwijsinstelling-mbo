import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_geen_r_of_1cho():
    for woord in ("Rscript", "staat1cho", "install.packages", "1cho_mbo", "cran."):
        assert woord not in README
    assert not re.search(r"\bR\b", README)


def test_installatie_is_uv_en_het_programma():
    stappen = README.split("## Installeren")[1].split("## Gebruiken")[0]
    nummers = re.findall(r"^\d+\. ", stappen, flags=re.MULTILINE)
    assert len(nummers) == 2
    assert "uv tool install" in stappen


def test_commandos_en_label():
    for tekst in (
        "smbo dashboard",
        "smbo staat",
        "smbo samenvoegen",
        "indicatief, geen oordeel",
        "Regeling studiesucces mbo",
    ):
        assert tekst.lower() in README.lower()


def test_links_naar_het_ontwerp_en_de_demodata_bestaan():
    for pad in re.findall(r"\]\(((?:docs|src)/[^)]+)\)", README):
        assert (ROOT / pad).exists(), pad


def test_crlf_en_todo_voor_de_video_blijven():
    ruw = (ROOT / "README.md").read_bytes()
    assert b"\r\n" in ruw and b"\n" not in ruw.replace(b"\r\n", b"")
    assert "<!-- TODO Aslam: nieuwe demovideo slepen -->" in README
