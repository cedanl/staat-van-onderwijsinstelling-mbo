"""Invoer → analyse op schijf: meldingen, tussenlaag en de tabellen van ``staat``."""

from pathlib import Path

from staat_mbo.analyse import Analyse, bereken, maak_analyse

BESTAND_MELDINGEN = "meldingen.txt"
BESTAND_RAPPORT = "stapelcontrole.json"
BESTAND_PEILMOMENTEN = "peilmomenten.parquet"
BESTAND_DIPLOMAS = "diplomas.parquet"
BESTANDEN_STAAT = {
    "studiesucces": "studiesucces.csv",
    "cohorten": "cohorten.csv",
    "loopbanen": "loopbanen.csv",
}


def _schrijf_meldingen(a: Analyse, uitvoer: Path) -> None:
    (uitvoer / BESTAND_MELDINGEN).write_text(
        "\n".join(a.regels()) + "\n", encoding="utf-8"
    )
    (uitvoer / BESTAND_RAPPORT).write_text(a.rapport.naar_json(), encoding="utf-8")


def _begin(invoer: list[Path], uitvoer: Path, oud: list[str]) -> Analyse:
    uitvoer.mkdir(parents=True, exist_ok=True)
    for naam in oud:
        (uitvoer / naam).unlink(missing_ok=True)
    return maak_analyse(invoer, uitvoer / "werk")


def samenvoegen(invoer: list[Path], uitvoer: Path) -> Analyse:
    """Voeg de invoer samen tot de mbo-tussenlaag, met meldingen en rapport.

    Meldingen en rapport worden altijd geschreven, de tussenlaag
    (``peilmomenten.parquet`` en ``diplomas.parquet``) alleen als het gelukt is.
    Die bestanden bevatten pseudoniemen: behandel ze als persoonsgegevens.
    """
    a = _begin(invoer, uitvoer, [BESTAND_PEILMOMENTEN, BESTAND_DIPLOMAS])
    if a.ok:
        a.peilmomenten.write_parquet(uitvoer / BESTAND_PEILMOMENTEN)
        a.diplomas.write_parquet(uitvoer / BESTAND_DIPLOMAS)
    _schrijf_meldingen(a, uitvoer)
    return a


def staat(invoer: list[Path], uitvoer: Path) -> Analyse:
    """Bereken de indicatoren, cohorten en loopbanen en schrijf ze als CSV.

    De CSV's bevatten alleen geaggregeerde cijfers.
    """
    a = _begin(invoer, uitvoer, list(BESTANDEN_STAAT.values()))
    if a.ok:
        resultaten = bereken(a)
        for veld, naam in BESTANDEN_STAAT.items():
            getattr(resultaten, veld).write_csv(uitvoer / naam)
    _schrijf_meldingen(a, uitvoer)
    return a
