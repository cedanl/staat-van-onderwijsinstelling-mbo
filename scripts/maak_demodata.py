"""Maak nep-RO-bestanden voor de demo: één instelling, tien schooljaren.

Verzonnen studenten, geen echte personen. Vast zaadgetal, dus elke run geeft
dezelfde bestanden. Een RO per twee schooljaren (2016-2017 t/m
2025-2026), zoals DUO ze levert. De studenten stapelen (n1 naar n2, n2 naar n3,
n3 naar n4), stromen op en af en volgen een crebo-vernieuwing.

    uv run python scripts/maak_demodata.py
"""

import random
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

DOEL = Path(__file__).parent.parent / "src" / "staat_mbo" / "demodata"
EERSTE_JAAR = 2016
LAATSTE_JAAR = 2025  # laatste schooljaar (2025-2026)
AANMAAK = date(2026, 10, 2)

## BRIN → (aanbieder, locatie, instroom per jaar, opleidingen (crebo, niveau)).
## Eén instelling: vijf RO's van twee jaar geven samen tien schooljaren.
INSTELLINGEN = {
    "27DV": (
        "100A501",
        "101X591",
        175,
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
## Kans op uitval per niveau en per opleiding erbovenop (sommige opleidingen
## doen het beter, andere slechter dan de norm).
UITVAL = {1: 0.32, 2: 0.24, 3: 0.20, 4: 0.20}
KWALITEIT = {
    25192: 0.12,
    25191: 0.20,
    25655: 0.18,
    25167: -0.05,
    25475: -0.04,
    25187: -0.04,
}
## Kansen op op- en afstromen zonder diploma en op stapelen na een diploma.
P_OPSTROMEN = {1: 0.0, 2: 0.07, 3: 0.06, 4: 0.0}
P_AFSTROMEN = {1: 0.0, 2: 0.05, 3: 0.05, 4: 0.04}
P_STAPELEN = {1: 0.55, 2: 0.30, 3: 0.22, 4: 0.0}
## Crebo-vernieuwing: wie vanaf dit jaar begint, start op het opvolgende crebo.
## De opvolgers staan ook in de referentiedata van de bekostigingsbestanden.
OPVOLGER = {
    25132: 25877,
    25167: 25808,
    25187: 25998,
    25191: 27015,
    25192: 25999,
    25225: 25883,
    25250: 25740,
    25475: 25780,
    25498: 25960,
    25655: 27145,
    25669: 27113,
}
VERNIEUWD = {
    25132: 2019,
    25167: 2021,
    25187: 2020,
    25191: 2022,
    25192: 2018,
    25225: 2023,
    25475: 2019,
    25498: 2021,
    25655: 2022,
    25669: 2020,
}


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
    wissels: int = 0
    stapels: int = 0
    inschrijvingen: list[Inschrijving] = field(default_factory=list)


def _schooljaar_start(jaar: int) -> date:
    return date(jaar, 8, 1)


def _kans(rng: random.Random, p: float) -> bool:
    return rng.random() < p


def _code(crebo: int, begin: date) -> int:
    """Crebo-vernieuwing: wie vanaf het vernieuwingsjaar begint, start op het nieuwe crebo."""
    jaar = VERNIEUWD.get(crebo)
    return OPVOLGER[crebo] if jaar is not None and begin.year >= jaar else crebo


def _na_einde(einde: date) -> date:
    """Begin van een vervolgopleiding: 1 augustus, of de dag na het einde als dat later is."""
    start = date(einde.year, 8, 1)
    return start if einde < start else einde + timedelta(days=1)


def _volg_opleiding(
    rng: random.Random,
    student: Student,
    crebo: int,
    niveau: int,
    traject: str,
    begin: date,
    trend: float,
    opleidingen: list[tuple[int, int]],
) -> None:
    """Eén inschrijving en wat daarna komt: uitval, wissel, op- of afstromen, diploma, stapelen."""
    duur = DUUR[niveau] + (1 if niveau == 4 and _kans(rng, 0.4) else 0)
    gepland = date(begin.year + duur, 7, 31)
    ins = Inschrijving(
        volgnummer=len(student.inschrijvingen) + 1,
        crebo=_code(crebo, begin),
        leertraject=traject,
        begin=begin,
        gepland=gepland,
    )
    student.inschrijvingen.append(ins)

    def vervolg(nieuw_niveau: int, na: date) -> None:
        kandidaten = [o for o in opleidingen if o[1] == nieuw_niveau and o[0] != crebo]
        if not kandidaten:
            return
        nieuw, nieuw_niveau = rng.choice(kandidaten)
        _volg_opleiding(
            rng, student, nieuw, nieuw_niveau, traject, na, trend, opleidingen
        )

    ## Lagere niveaus vallen vaker uit; de trend verbetert de laatste jaren.
    p_uitval = max(0.03, UITVAL[niveau] + KWALITEIT.get(crebo, 0.0) - trend)
    mag_wisselen = student.wissels == 0
    p_op = P_OPSTROMEN[niveau] if mag_wisselen else 0.0
    p_af = P_AFSTROMEN[niveau] if mag_wisselen else 0.0
    p_zij = 0.05 if mag_wisselen else 0.0
    keuze = rng.random()
    if keuze < p_uitval:
        jaren = 1 if _kans(rng, 0.65) else rng.randint(2, max(2, duur))
        ins.einde = begin + timedelta(days=rng.randint(60, 300) + 365 * (jaren - 1))
        ins.reden = REDEN_UITVAL
        return
    keuze -= p_uitval
    for p, nieuw_niveau in (
        (p_op, niveau + 1),
        (p_af, niveau - 1),
        (p_zij, niveau),
    ):
        if keuze < p:
            ## Wissel zonder diploma, halverwege of aan het eind van het eerste jaar.
            ins.einde = date(begin.year + 1, rng.choice([1, 7, 7]), 31)
            ins.reden = REDEN_WISSEL
            student.wissels += 1
            vervolg(nieuw_niveau, ins.einde + timedelta(days=1))
            return
        keuze -= p
    ## Diploma: meestal op tijd, soms een jaar of twee later, soms in augustus of september.
    vertraging = rng.choices([0, 1, 2], weights=[70, 22, 8])[0]
    maand = rng.choice([6, 7, 7, 7, 7, 8, 9])
    diploma = date(gepland.year + vertraging, maand, rng.randint(1, 28))
    ins.diploma = diploma
    ins.einde = diploma + timedelta(days=rng.randint(0, 20))
    ins.reden = REDEN_DIPLOMA
    if vertraging:
        ins.gepland = date(diploma.year, 7, 31)
    ## Stapelen: na het diploma meteen door op het niveau erboven.
    if student.stapels < 2 and _kans(rng, P_STAPELEN[niveau]):
        student.stapels += 1
        vervolg(niveau + 1, _na_einde(ins.einde))


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
