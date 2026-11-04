"""Meldingen bij te weinig historie in de bestanden (ontwerp §7)."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from staat_mbo.indicatoren import (
    STARTERS_JAREN_TERUG,
    sr_terugblik,
    volledig,
    waarneembare_jaren,
)
from staat_mbo.waarneming import Waarneming

## Aantal aaneengesloten 1 oktobers dat een driejaarscijfer minimaal nodig heeft.
_NODIG = {"jr": 4, "dr": 4, "sr": 5}
## Rendement nominaal + 1 op niveau 4 (duur 4): cohort t tot en met t + 5.
_RENDEMENT_OKTOBERS = 6


@dataclass(frozen=True)
class Melding:
    ernst: str  # "info" of "waarschuwing"
    tekst: str


def _langste_reeks(w: Waarneming) -> int:
    """Langste reeks aaneengesloten waarneembare 1 oktobers."""
    langste = huidig = 0
    for jaar in range(w.eerste_jaar, w.laatste_jaar + 1):
        huidig = huidig + 1 if w.waarneembaar(jaar) else 0
        langste = max(langste, huidig)
    return langste


def _perioden(indicator: str, w: Waarneming) -> list[int]:
    """Laatste jaartijdvak t van elk driejaarscijfer dat te berekenen is."""
    jaren = set(waarneembare_jaren(indicator, w))
    return sorted(t for t in jaren if {t - 2, t - 1} <= jaren)


def _jaren_tekst(jaren: Iterable[int], label: Callable[[int], str] = str) -> str:
    """Opeenvolgende jaren als "2022 t/m 2024", losse jaren met een komma."""
    delen: list[list[int]] = []
    for jaar in sorted(jaren):
        if delen and jaar == delen[-1][-1] + 1:
            delen[-1].append(jaar)
        else:
            delen.append([jaar])
    return ", ".join(
        label(d[0]) if len(d) == 1 else f"{label(d[0])} t/m {label(d[-1])}"
        for d in delen
    )


def _volledig(indicator: str, w: Waarneming, t: int) -> bool:
    """Is het driejaarscijfer met laatste jaartijdvak t volledig?"""
    return all(volledig(indicator, w, y) for y in (t - 2, t - 1, t))


def _nog_geen(naam: str, indicator: str, w: Waarneming) -> Melding:
    return Melding(
        "waarschuwing",
        f"{naam}: nog geen driejaarscijfer. Je hebt {_langste_reeks(w)} "
        f"aaneengesloten 1 oktobers, er zijn er minstens {_NODIG[indicator]} nodig.",
    )


def meldingen(w: Waarneming) -> list[Melding]:
    """Meldingen over wat de dekking van de bestanden voor de cijfers betekent."""
    uit: list[Melding] = []

    zonder = [
        t
        for t in range(w.eerste_jaar, w.laatste_jaar)
        if w.gaten and not w.reeks(t, t + 1)
    ]
    if zonder:
        uit.append(
            Melding(
                "waarschuwing",
                f"Door het gat in de leveringen (1 oktober {_jaren_tekst(w.gaten)}) "
                f"ontbreken de cijfers van de jaartijdvakken "
                f"{_jaren_tekst(zonder, lambda t: f'{t}-{t + 1}')}.",
            )
        )

    perioden = {i: _perioden(i, w) for i in _NODIG}
    if not perioden["jr"]:
        uit.append(_nog_geen("Jaarresultaat", "jr", w))

    if not perioden["dr"]:
        uit.append(_nog_geen("Diplomaresultaat", "dr", w))
    elif not _volledig("dr", w, perioden["dr"][-1]):
        onvolledig = [t for t in perioden["dr"] if not _volledig("dr", w, t)]
        uit.append(
            Melding(
                "waarschuwing",
                f"Diplomaresultaat: diploma's van vóór {w.diplomas_vanaf:%d-%m-%Y} "
                "zitten niet in je bestanden. Voor de driejaarscijfers met laatste "
                f"jaartijdvak {_jaren_tekst(onvolledig)} ontbreken diploma's uit de "
                "5 jaar terug; daar is het cijfer een ondergrens. Upload oudere "
                "RO's voor een volledig cijfer.",
            )
        )

    if not perioden["sr"]:
        uit.append(_nog_geen("Startersresultaat", "sr", w))
    elif not _volledig("sr", w, perioden["sr"][-1]):
        k = sr_terugblik(w, perioden["sr"][-1])
        geleden = (
            f"{k + 1}-{STARTERS_JAREN_TERUG}"
            if k + 1 < STARTERS_JAREN_TERUG
            else str(STARTERS_JAREN_TERUG)
        )
        uit.append(
            Melding(
                "waarschuwing",
                f"Startersresultaat: we kijken {k} jaar terug in plaats van "
                f"{STARTERS_JAREN_TERUG}. Wie {geleden} jaar geleden al eens bij je "
                "stond en terugkomt, telt als nieuwe student.",
            )
        )

    eerste = next(
        (
            t
            for t in range(w.eerste_jaar, w.laatste_jaar + 1)
            if w.reeks(t, t + _RENDEMENT_OKTOBERS - 1)
        ),
        None,
    )
    if eerste is None:
        uit.append(
            Melding(
                "info",
                "Rendement nominaal + 1 voor niveau 4 is nog niet te zien: daarvoor "
                f"zijn {_RENDEMENT_OKTOBERS} aaneengesloten 1 oktobers nodig, je hebt "
                f"er {_langste_reeks(w)}.",
            )
        )
    else:
        uit.append(
            Melding(
                "info",
                f"Rendement nominaal + 1 voor niveau 4 is pas te zien vanaf cohort {eerste}.",
            )
        )
    return uit
