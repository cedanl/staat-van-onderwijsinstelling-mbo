"""Invoer → gecontroleerde 1CHO-vorm, met meldingen voor de gebruiker."""

from pathlib import Path

from staat_mbo.bron import InvoerFout, laad_star
from staat_mbo.naar_1cho import (
    MIN_INSCHRIJVINGEN_DUUR,
    naar_1cho,
    nominale_duur,
    opleidingen_met_standaardduur,
    schrijf_1cho,
)
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
            duur = nominale_duur(star)
            df = naar_1cho(star, duur)
            zonder, totaal = opleidingen_met_standaardduur(df, duur)
            if zonder:
                rapport.waarschuwingen.append(
                    f"{zonder} van de {totaal} opleidingen (per leerweg) hebben minder "
                    f"dan {MIN_INSCHRIJVINGEN_DUUR} inschrijvingen om de nominale duur "
                    "uit de geplande einddatum te halen; daar geldt de standaardduur "
                    "per niveau (1, 2, 3 of 4 jaar)."
                )
            schrijf_1cho(df, uitvoer / BESTAND_1CHO)
    except InvoerFout as e:
        rapport = Stapelrapport([], [], [], 0, fouten=[str(e)])
    (uitvoer / BESTAND_MELDINGEN).write_text(
        "\n".join(rapport.meldingen()) + "\n", encoding="utf-8"
    )
    (uitvoer / BESTAND_RAPPORT).write_text(rapport.naar_json(), encoding="utf-8")
    return rapport
