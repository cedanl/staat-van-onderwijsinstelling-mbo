"""Controle op de gestapelde leveringen: dekking, gaten en meldingen."""

import json
from dataclasses import asdict, dataclass, field
from datetime import timedelta

import polars as pl

_MIN_JAREN = 5


@dataclass
class Stapelrapport:
    brins: list[str]
    instellingen: list[str]
    schooljaren: list[int]
    aantal_studenten: int
    gaten: list[dict] = field(default_factory=list)
    fouten: list[str] = field(default_factory=list)
    waarschuwingen: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.fouten

    def meldingen(self) -> list[str]:
        """Regels voor de gebruiker; de eerste zegt of het gelukt is."""
        if not self.ok:
            return ["Niet gelukt.", *self.fouten]
        jaren = f"{self.schooljaren[0]}–{self.schooljaren[-1]}"
        return [
            "Gelukt: de bestanden zijn samengevoegd tot één bestand.",
            f"Instellingen (BRIN): {', '.join(self.brins)}",
            f"Schooljaren: {jaren} ({len(self.schooljaren)} jaar)",
            f"Studenten: {self.aantal_studenten}",
            *(f"Let op: {w}" for w in self.waarschuwingen),
        ]

    def naar_json(self) -> str:
        return json.dumps(
            {**asdict(self), "ok": self.ok}, ensure_ascii=False, indent=2
        )


def _gaten(leveringen: pl.DataFrame) -> list[dict]:
    ro = leveringen.filter(pl.col("DatumBeginPeriode").is_not_null()).sort(
        "BRIN", "DatumBeginPeriode"
    )
    gaten = []
    for (brin,), groep in ro.group_by("BRIN", maintain_order=True):
        rijen = groep.select("DatumBeginPeriode", "DatumEindePeriode").rows()
        for (_, einde), (begin, _) in zip(rijen, rijen[1:]):
            if begin > einde + timedelta(days=1):
                gaten.append(
                    {"brin": brin, "na": einde.isoformat(), "voor": begin.isoformat()}
                )
    return gaten


def controleer_stapel(star: dict[str, pl.DataFrame]) -> Stapelrapport:
    feit = star["fact_inschrijving_schooljaar"]
    namen = sorted(set(star["dim_instelling"]["Instelling_naam"].drop_nulls()))
    rapport = Stapelrapport(
        brins=sorted(set(feit["BRIN"].drop_nulls())),
        instellingen=namen,
        schooljaren=sorted(set(feit["Schooljaar"].drop_nulls())),
        aantal_studenten=feit["_persoon_id"].n_unique(),
        gaten=_gaten(star["meta_leveringen"]),
    )
    if feit.is_empty():
        rapport.fouten.append(
            "Er staan geen inschrijvingen op 1 oktober in de bestanden. "
            "Controleer of je de RO-bestanden hebt geüpload."
        )
        return rapport
    for g in rapport.gaten:
        rapport.waarschuwingen.append(
            f"gat in de leveringen van {g['brin']} tussen {g['na']} en {g['voor']}; "
            "rendement en uitval rond dit gat zijn onbetrouwbaar."
        )
    if len(namen) > 1:
        rapport.waarschuwingen.append(
            f"de bestanden horen bij {', '.join(namen)}; ze tellen als één bestuur."
        )
    if len(rapport.schooljaren) < _MIN_JAREN:
        rapport.waarschuwingen.append(
            f"minder dan {_MIN_JAREN} schooljaren; "
            "rendement na 5 jaar is nog niet te zien."
        )
    return rapport
