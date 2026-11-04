"""Controle op de gestapelde leveringen: dekking, gaten en meldingen."""

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from itertools import pairwise

import polars as pl


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
        return json.dumps({**asdict(self), "ok": self.ok}, ensure_ascii=False, indent=2)


def gaten(leveringen: pl.DataFrame) -> list[dict]:
    ro = leveringen.filter(pl.col("DatumBeginPeriode").is_not_null()).sort(
        "BRIN", "DatumBeginPeriode"
    )
    gaten = []
    for (brin,), groep in ro.group_by("BRIN", maintain_order=True):
        rijen = groep.select("DatumBeginPeriode", "DatumEindePeriode").rows()
        for (_, einde), (begin, _) in pairwise(rijen):
            if begin > einde + timedelta(days=1):
                gaten.append(
                    {"brin": brin, "na": einde.isoformat(), "voor": begin.isoformat()}
                )
    return gaten


def _ongelijk_einde(leveringen: pl.DataFrame) -> list[str]:
    """BRIN's die eerder ophouden dan de rest.

    Alle cijfers rekenen tot de laatste 1 oktober die elke BRIN dekt; wat een
    BRIN daarna nog levert, doet niet mee.
    """
    if "Laatste_peildatum" not in leveringen.columns:
        return []
    einde = (
        leveringen.filter(pl.col("BRIN").is_not_null())
        .group_by("BRIN")
        .agg(pl.col("Laatste_peildatum").max())
        .drop_nulls()
        .sort("BRIN")
    )
    if einde.is_empty():
        return []
    laatste = einde["Laatste_peildatum"].max()
    tot = einde["Laatste_peildatum"].min().year
    return [
        f"de bestanden van {brin} lopen tot {datum:%d-%m-%Y}, de rest tot "
        f"{laatste:%d-%m-%Y}; we rekenen tot {tot}, het vroegste einde. Upload "
        "ook de nieuwste RO van deze BRIN voor latere jaren."
        for brin, datum in einde.iter_rows()
        if datum < laatste
    ]


def _eerste_1_oktober(datum: date) -> int:
    return datum.year if datum <= date(datum.year, 10, 1) else datum.year + 1


def _beginjaren(leveringen: pl.DataFrame) -> dict[str, int]:
    """Per BRIN de eerste 1 oktober in zijn RO's."""
    begin = (
        leveringen.filter(pl.col("DatumBeginPeriode").is_not_null())
        .group_by("BRIN")
        .agg(pl.col("DatumBeginPeriode").min())
        .sort("BRIN")
    )
    return {b: _eerste_1_oktober(d) for b, d in begin.iter_rows()}


def _ongelijk_begin(leveringen: pl.DataFrame) -> list[str]:
    """BRIN's die later beginnen dan de rest.

    Alle cijfers rekenen vanaf de eerste 1 oktober die elke BRIN dekt; wat de
    andere BRIN's daarvoor leveren, doet niet mee.
    """
    jaren = _beginjaren(leveringen)
    if len(jaren) < 2:
        return []
    vanaf, vroegst = max(jaren.values()), min(jaren.values())
    return [
        f"de bestanden van {brin} beginnen pas op 1 oktober {jaar}, de rest op "
        f"1 oktober {vroegst}; we rekenen vanaf {vanaf}, het laatste begin. Upload "
        "ook de oudere RO's van deze BRIN, of laat deze BRIN weg voor een langere "
        "reeks."
        for brin, jaar in jaren.items()
        if jaar > vroegst
    ]


def _geen_gedeelde_jaren(leveringen: pl.DataFrame) -> list[str]:
    """Geen enkele 1 oktober die alle BRIN's dekken: dan valt er niets te rekenen."""
    jaren = _beginjaren(leveringen)
    if not jaren or "Laatste_peildatum" not in leveringen.columns:
        return []
    einde = (
        leveringen.filter(pl.col("BRIN").is_not_null())
        .group_by("BRIN")
        .agg(pl.col("Laatste_peildatum").max())
        .drop_nulls()
    )
    if einde.is_empty() or max(jaren.values()) <= einde["Laatste_peildatum"].min().year:
        return []
    return [
        (
            "de BRIN's hebben geen 1 oktober gemeen, dus er valt niets te berekenen. "
            "Upload voor elke BRIN dezelfde schooljaren, of upload de BRIN's apart."
        )
    ]


def controleer_stapel(star: dict[str, pl.DataFrame]) -> Stapelrapport:
    feit = star["fact_inschrijving_schooljaar"]
    namen = sorted(set(star["dim_instelling"]["Instelling_naam"].drop_nulls()))
    rapport = Stapelrapport(
        brins=sorted(set(feit["BRIN"].drop_nulls())),
        instellingen=namen,
        schooljaren=sorted(set(feit["Schooljaar"].drop_nulls())),
        aantal_studenten=feit["_persoon_id"].n_unique(),
        gaten=gaten(star["meta_leveringen"]),
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
    meta = star["meta_leveringen"]
    rapport.waarschuwingen += _geen_gedeelde_jaren(meta)
    rapport.waarschuwingen += _ongelijk_begin(meta)
    rapport.waarschuwingen += _ongelijk_einde(meta)
    if len(namen) > 1:
        rapport.waarschuwingen.append(
            f"de bestanden horen bij {', '.join(namen)}; ze tellen als één bestuur."
        )
    return rapport
