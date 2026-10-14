"""Invoer → gecontroleerde 1CHO-vorm, met meldingen voor de gebruiker."""

from pathlib import Path

from staat_mbo.bron import InvoerFout, laad_star
from staat_mbo.naar_1cho import naar_1cho, schrijf_1cho
from staat_mbo.stapelcontrole import Stapelrapport, controleer_stapel

BESTAND_1CHO = "1cho_mbo.csv"
BESTAND_MELDINGEN = "meldingen.txt"
BESTAND_RAPPORT = "stapelcontrole.json"


def samenvoegen(invoer: list[Path], uitvoer: Path) -> Stapelrapport:
    """Voeg de invoer samen tot ``1cho_mbo.csv`` met meldingen en rapport.

    Meldingen en rapport worden altijd geschreven, het 1CHO-bestand alleen
    als het gelukt is.
    """
    uitvoer.mkdir(parents=True, exist_ok=True)
    (uitvoer / BESTAND_1CHO).unlink(missing_ok=True)
    try:
        star = laad_star(invoer, uitvoer / "werk")
        rapport = controleer_stapel(star)
        if rapport.ok:
            schrijf_1cho(naar_1cho(star), uitvoer / BESTAND_1CHO)
    except InvoerFout as e:
        rapport = Stapelrapport([], [], [], 0, fouten=[str(e)])
    (uitvoer / BESTAND_MELDINGEN).write_text(
        "\n".join(rapport.meldingen()) + "\n", encoding="utf-8"
    )
    (uitvoer / BESTAND_RAPPORT).write_text(rapport.naar_json(), encoding="utf-8")
    return rapport
