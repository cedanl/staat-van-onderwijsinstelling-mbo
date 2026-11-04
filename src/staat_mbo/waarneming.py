"""Welke 1 oktobers we in de bestanden kunnen waarnemen (ontwerp §4)."""

from dataclasses import dataclass, field
from datetime import date

import polars as pl

from staat_mbo.stapelcontrole import gaten


@dataclass
class Waarneming:
    """Dekking van de bestanden, per instelling (alle BRIN's samen)."""

    eerste_jaar: int
    laatste_jaar: int
    diplomas_vanaf: date
    gaten: list[int] = field(default_factory=list)

    def waarneembaar(self, jaar: int) -> bool:
        """Is de 1 oktober van ``jaar`` gedekt, en ligt hij niet in een gat?"""
        return self.eerste_jaar <= jaar <= self.laatste_jaar and jaar not in self.gaten

    def reeks(self, van: int, tot: int) -> bool:
        """Zijn alle 1 oktobers van ``van`` t/m ``tot`` waarneembaar?"""
        return all(self.waarneembaar(j) for j in range(van, tot + 1))


def _eerste_1_oktober(datum: date) -> int:
    """Jaar van de eerste 1 oktober op of na ``datum``."""
    return datum.year if datum <= date(datum.year, 10, 1) else datum.year + 1


def _gatjaren(leveringen: pl.DataFrame) -> list[int]:
    jaren: set[int] = set()
    for g in gaten(leveringen):
        na, voor = date.fromisoformat(g["na"]), date.fromisoformat(g["voor"])
        jaren |= {
            j for j in range(na.year, voor.year + 1) if na < date(j, 10, 1) < voor
        }
    return sorted(jaren)


def waarneming(star: dict[str, pl.DataFrame]) -> Waarneming:
    """Bepaal uit ``meta_leveringen`` welke 1 oktobers betrouwbaar zijn.

    Eerste jaar: de eerste 1 oktober die elke BRIN dekt. Laatste jaar: de
    laatste 1 oktober die elke BRIN dekt (het vroegste einde). Leveringen
    zonder periode (TBG-i) tellen niet mee voor het begin.
    """
    meta = star["meta_leveringen"]
    ro = meta.filter(pl.col("DatumBeginPeriode").is_not_null())
    if ro.is_empty():
        raise ValueError("Geen RO-leveringen: de dekking is niet te bepalen.")
    begin = ro.group_by("BRIN").agg(pl.col("DatumBeginPeriode").min())
    einde = (
        meta.filter(pl.col("BRIN").is_not_null())
        .group_by("BRIN")
        .agg(pl.col("Laatste_peildatum").max())
        .drop_nulls()
    )
    return Waarneming(
        eerste_jaar=max(_eerste_1_oktober(d) for d in begin["DatumBeginPeriode"]),
        laatste_jaar=min(d.year for d in einde["Laatste_peildatum"]),
        diplomas_vanaf=ro["DatumBeginPeriode"].min(),
        gaten=_gatjaren(meta),
    )
