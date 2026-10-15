"""Maak nep-RO-bestanden voor de demo: één instelling, zes schooljaren.

Verzonnen studenten, geen echte personen. Vast zaadgetal, dus elke run geeft
dezelfde bestanden. Een RO per twee schooljaren (2020-2021 t/m
2024-2025), zoals DUO ze levert.

    uv run python scripts/maak_demodata.py
"""

import random
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

DOEL = Path(__file__).parent.parent / "demodata"
EERSTE_JAAR = 2020
LAATSTE_JAAR = 2025  # laatste schooljaar (2025-2026)
AANMAAK = date(2026, 10, 2)

## BRIN → (aanbieder, locatie, instroom per jaar, opleidingen (crebo, niveau)).
## Eén instelling: drie RO's van twee jaar geven samen zes schooljaren.
INSTELLINGEN = {
    "27DV": (
        "100A501",
        "101X591",
        310,
        [
            (25655, 4),
            (25475, 3),
            (25498, 2),
            (25187, 4),
            (25191, 3),
            (25192, 2),
            (25669, 3),
            (25225, 2),
            (25132, 4),
            (25167, 2),
            (25250, 1),
        ],
    ),
}
DUUR = {1: 1, 2: 2, 3: 3, 4: 3}
## Uitschrijfredenen (codes uit de demo-RO's): 08 diploma, 02 overstap, 01 uitval.
REDEN_DIPLOMA, REDEN_WISSEL, REDEN_UITVAL = "08", "02", "01"


@dataclass
class Inschrijving:
    volgnummer: int
    crebo: int
    leertraject: str
    begin: date
    gepland: date
    einde: date | None = None
    reden: str | None = None
    diploma: date | None = None


@dataclass
class Student:
    nummer: int
    brin: str
    geboortedatum: date
    geslacht: str
    inschrijvingen: list[Inschrijving] = field(default_factory=list)


def _schooljaar_start(jaar: int) -> date:
    return date(jaar, 8, 1)


def _kans(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def _volg_opleiding(
    rng: random.Random,
    student: Student,
    crebo: int,
    niveau: int,
    traject: str,
    begin: date,
    trend: float,
    mag_wisselen: bool,
    opleidingen: list[tuple[int, int]],
) -> None:
    duur = DUUR[niveau] + (1 if niveau == 4 and _kans(rng, 0.4) else 0)
    gepland = date(begin.year + duur, 7, 31)
    ins = Inschrijving(
        volgnummer=len(student.inschrijvingen) + 1,
        crebo=crebo,
        leertraject=traject,
        begin=begin,
        gepland=gepland,
    )
    student.inschrijvingen.append(ins)

    ## Lagere niveaus vallen vaker uit; de trend verbetert de laatste jaren.
    p_uitval = {1: 0.30, 2: 0.22, 3: 0.16, 4: 0.12}[niveau] - trend
    p_wissel = 0.12 if mag_wisselen else 0.0
    keuze = rng.random()
    if keuze < p_uitval:
        jaren = 1 if _kans(rng, 0.65) else rng.randint(2, max(2, duur))
        ins.einde = begin + timedelta(days=rng.randint(60, 300) + 365 * (jaren - 1))
        ins.reden = REDEN_UITVAL
        return
    if keuze < p_uitval + p_wissel:
        ## Wissel halverwege of aan het eind van het eerste jaar.
        ins.einde = date(begin.year + 1, rng.choice([1, 7, 7]), 31)
        ins.reden = REDEN_WISSEL
        andere = [o for o in opleidingen if o[0] != crebo]
        nieuw, nieuw_niveau = rng.choice(andere)
        nieuw_begin = ins.einde + timedelta(days=1)
        _volg_opleiding(
            rng,
            student,
            nieuw,
            nieuw_niveau,
            traject,
            nieuw_begin,
            trend,
            False,
            opleidingen,
        )
        return
    ## Diploma: meestal op tijd, soms een jaar of twee later.
    vertraging = rng.choices([0, 1, 2], weights=[70, 22, 8])[0]
    diploma = date(gepland.year + vertraging, rng.choice([6, 7]), rng.randint(1, 28))
    ins.diploma = diploma
    ins.einde = diploma + timedelta(days=rng.randint(0, 20))
    ins.reden = REDEN_DIPLOMA
    if vertraging:
        ins.gepland = date(diploma.year, 7, 31)


def maak_studenten(rng: random.Random) -> list[Student]:
    studenten: list[Student] = []
    nummer = 0
    for brin, (_, _, instroom, opleidingen) in INSTELLINGEN.items():
        for jaar in range(EERSTE_JAAR, LAATSTE_JAAR + 1):
            trend = 0.01 * (jaar - EERSTE_JAAR) * 0.5
            aantal = int(instroom * rng.uniform(0.9, 1.1))
            for _ in range(aantal):
                nummer += 1
                crebo, niveau = rng.choice(opleidingen)
                bbl = _kans(rng, 0.25)
                begin = (
                    _schooljaar_start(jaar)
                    if not bbl or _kans(rng, 0.6)
                    else date(jaar, rng.choice([9, 9, 10]), rng.randint(1, 28))
                )
                leeftijd = rng.randint(16, 19) if not bbl else rng.randint(18, 40)
                student = Student(
                    nummer=nummer,
                    brin=brin,
                    geboortedatum=date(
                        jaar - leeftijd, rng.randint(1, 12), rng.randint(1, 28)
                    ),
                    geslacht=rng.choice("MV"),
                )
                _volg_opleiding(
                    rng,
                    student,
                    crebo,
                    niveau,
                    "BBL" if bbl else "BOL",
                    begin,
                    trend,
                    True,
                    opleidingen,
                )
                studenten.append(student)
    return studenten


def _d(datum: date | None) -> str:
    return datum.isoformat() if datum else ""


def _overlapt(ins: Inschrijving, begin: date, einde: date) -> bool:
    return ins.begin <= einde and (ins.einde is None or ins.einde >= begin)


def schrijf_ro(studenten: list[Student], brin: str, begin: date, einde: date) -> Path:
    aanbieder, locatie, _, _ = INSTELLINGEN[brin]
    regels = [f"VLP|{brin}|{_d(begin)}|{_d(einde)}|{_d(AANMAAK)}"]
    tel = {"PER": 0, "ISG": 0, "ISP": 0, "DIP": 0}
    resultaat = 0
    for s in studenten:
        if s.brin != brin:
            continue
        zichtbaar = [i for i in s.inschrijvingen if _overlapt(i, begin, einde)]
        if not zichtbaar:
            continue
        bsn = f"BSN{s.nummer}"
        regels.append(f"PER|{bsn}||{_d(s.geboortedatum)}|{s.geslacht}")
        tel["PER"] += 1
        for i in zichtbaar:
            ## Na de periode is de uitschrijving nog niet bekend.
            bekend = i.einde is not None and i.einde <= einde
            werkelijk = _d(i.einde) if bekend else ""
            reden = i.reden if bekend else ""
            staart = f"|{werkelijk}|{reden}" if werkelijk else ""
            regels.append(
                f"ISG|{bsn}||{i.volgnummer}|{_d(i.begin)}|{_d(i.gepland)}{staart}"
            )
            regels.append(
                f"ISP|{bsn}||{i.volgnummer}|{_d(i.begin)}|{i.crebo}|{i.leertraject}"
                f"||J||{aanbieder}|{locatie}||"
            )
            tel["ISG"] += 1
            tel["ISP"] += 1
            if i.diploma and begin <= i.diploma <= einde:
                resultaat += 1
                regels.append(
                    f"DIP|{bsn}||{s.nummer * 10 + i.volgnummer}|{i.crebo}"
                    f"|{_d(i.diploma)}||J|{i.volgnummer}|{aanbieder}"
                )
                tel["DIP"] += 1
    regels.append(f"SLR|{tel['PER']}|{tel['ISG']}|{tel['ISP']}|0|0|{tel['DIP']}|0|0|0")
    pad = DOEL / f"RO_{brin}_{begin:%Y%m%d}_{einde:%Y%m%d}.csv"
    pad.write_text("\n".join(regels) + "\n", encoding="utf-8")
    return pad


def main() -> None:
    rng = random.Random(2026)
    studenten = maak_studenten(rng)
    if DOEL.exists():
        shutil.rmtree(DOEL)
    DOEL.mkdir()
    for brin in INSTELLINGEN:
        for jaar in range(EERSTE_JAAR, LAATSTE_JAAR + 1, 2):
            schrijf_ro(studenten, brin, date(jaar, 8, 1), date(jaar + 2, 7, 31))
    print(f"{len(studenten)} studenten in {len(list(DOEL.iterdir()))} bestanden")


if __name__ == "__main__":
    main()
