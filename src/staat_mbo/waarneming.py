"""Welke 1 oktobers we in de bestanden kunnen waarnemen (ontwerp §4)."""

from dataclasses import dataclass, field
from datetime import date


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
