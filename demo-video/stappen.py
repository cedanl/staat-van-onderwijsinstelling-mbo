"""Stappen van de demovideo: ondertitel en chip per stap (zonder geluid).

Eén bron voor record.py en stitch.py. De ondertitel is hooguit 110 tekens
(tests/test_demo_stappen.py); ``leestijd`` bepaalt hoe lang een stap in beeld blijft.

CHIPS: per stap (label, toelichting, kleur) voor het kader met pijl in de app.
WAARDEN en STUDIESUCCES: getallen zoals ze op de pagina moeten staan; record.py
controleert ze tegen het scherm, zodat tekst en beeld kloppen.
"""

STAPPEN = [
    (
        "start",
        "Het dashboard rekent het studiesucces van je instelling na, op basis van je eigen RO-bestanden.",
    ),
    (
        "privacy",
        "Je bestanden blijven op je eigen computer en persoonsnummers krijgen een code.",
    ),
    (
        "kies",
        "Kies met de bestandskiezer al je RO-bestanden tegelijk: hier vijf bestanden over tien jaar.",
    ),
    (
        "samenvoegen",
        "Klik op Samenvoegen: de bestanden worden gecontroleerd en tot één geheel gemaakt.",
    ),
    (
        "gelukt",
        "Gelukt: je ziet voor welke instelling, welke schooljaren en hoeveel studenten het geldt.",
    ),
    (
        "meldingen",
        "Meldingen vertellen wat er aan je bestanden opvalt, zoals een cohort dat nog te kort loopt.",
    ),
    (
        "studenten",
        "In je bestanden: 1.743 verschillende studenten, alle niveaus en leerwegen.",
    ),
    ("schooljaren", "10 schooljaren: elke 1 oktober van 2016 t/m 2025 staat erin."),
    (
        "ingeschreven",
        "564 studenten ingeschreven op de laatste peildatum, 1 oktober 2025.",
    ),
    ("diplomas", "953 diploma's in je bestanden, ook van studenten die nog studeren."),
    (
        "opleidingen",
        "11 opleidingen (crebo's): een crebo-vernieuwing telt als dezelfde opleiding.",
    ),
    ("brin", "1 BRIN-nummer. Heb je er meer, dan tellen ze samen als één instelling."),
    (
        "indicatoren",
        "Jaarresultaat 67,9%, diplomaresultaat 68,9%, startersresultaat 80,7%: de Regeling studiesucces mbo.",
    ),
    (
        "tabel",
        "Per opleiding zie je de cijfers en de norm. Bij minder dan 12 studenten staat geen percentage.",
    ),
    (
        "norm",
        "Per niveau zie je het verloop. De stippellijn is de neutrale norm uit de regeling, geen oordeel.",
    ),
    (
        "filter",
        "Met de filters links kijk je naar één niveau, leerweg, domein of opleiding.",
    ),
    ("gefilterd", "Hier alleen niveau 4: de cijfers veranderen mee."),
    (
        "instroomcohort",
        "Cohorten: hoeveel studenten instromen, en waar ze vandaan komen.",
    ),
    (
        "rendement",
        "Rendement nominaal en nominaal + 1. Grijs betekent: nog niet waarneembaar.",
    ),
    ("uitvalcohort", "Uitval per cohort, na 1 jaar en na de nominale duur."),
    (
        "loopbanen",
        "Loopbanen: waar studenten na 1, 2 of 3 jaar staan. Stapelen telt niet als uitval of wissel.",
    ),
    ("niveaus", "Stapelen, opstromen en afstromen: dit onderscheidt het mbo."),
    (
        "over",
        "Over de cijfers legt de definities uit, noemt de bronnen en toont wat je bestanden dekken.",
    ),
    (
        "indicatief",
        "Indicatief: berekend op je eigen RO's, niet op het register van de Inspectie. Geen oordeel.",
    ),
]

## (label, toelichting, kleur); ontbreekt een stap, dan krijgt hij alleen een kader.
CHIPS = {
    "start": (
        "Wat het doet",
        "Studiesucces, cohorten en loopbanen, berekend op je eigen bestanden.",
        "blauw",
    ),
    "privacy": (
        "Blijft lokaal",
        "Persoonsnummers krijgen een code. Behandel alles als persoonsgegevens.",
        "groen",
    ),
    "kies": (
        "1 · Kies je bestanden",
        "Echt uploaden: de vijf RO's staan in de lijst.",
        "blauw",
    ),
    "samenvoegen": (
        "2 · Samenvoegen",
        "Controleert de bestanden en voegt ze samen.",
        "blauw",
    ),
    "gelukt": ("Gelukt", "Instelling, schooljaren en aantal studenten.", "groen"),
    "meldingen": (
        "Meldingen",
        "Wat er aan je bestanden opvalt, en wat dat voor de cijfers betekent.",
        "oranje",
    ),
    "studenten": ("In je bestanden", "Tellingen, zonder definitiekeuzes.", "blauw"),
    "schooljaren": ("Schooljaren", "Elke 1 oktober in je bestanden.", "blauw"),
    "ingeschreven": ("Laatste peildatum", "Ingeschreven op 1 oktober 2025.", "blauw"),
    "diplomas": ("Diploma's", "Alle diploma's in je bestanden.", "groen"),
    "opleidingen": (
        "Opleidingen",
        "Crebo's; een vernieuwing telt als dezelfde.",
        "blauw",
    ),
    "brin": ("BRIN-nummers", "Samen één instelling.", "blauw"),
    "indicatoren": (
        "Regeling studiesucces",
        "Driejaarscijfers over 2022-23 t/m 2024-25.",
        "blauw",
    ),
    "tabel": (
        "n < 12: geen percentage",
        "Te weinig studenten voor een betrouwbaar cijfer.",
        "oranje",
    ),
    "norm": (
        "Neutrale norm",
        "Per niveau een stippellijn om naast te leggen.",
        "blauw",
    ),
    "gefilterd": ("Alleen niveau 4", "Alle cijfers volgen het filter.", "groen"),
    "instroomcohort": (
        "Instroom naar herkomst",
        "Nieuw, na diploma, ander niveau of wissel.",
        "blauw",
    ),
    "rendement": (
        "Grijs = nog niet te zien",
        "Het cohort is nog te kort te volgen.",
        "oranje",
    ),
    "uitvalcohort": ("Uitval", "Na 1 jaar en na de nominale duur.", "oranje"),
    "loopbanen": ("Loopbaanstatus", "Waar studenten na 1, 2 of 3 jaar staan.", "blauw"),
    "niveaus": ("Het mbo-eigene", "Stapelen, opstromen en afstromen.", "groen"),
    "over": (
        "Definities en bronnen",
        "Wat elk cijfer betekent en wat je bestanden dekken.",
        "blauw",
    ),
    "indicatief": (
        "Geen oordeel",
        "Eigen RO's, niet het register van de Inspectie.",
        "oranje",
    ),
}

## Tegels op Start, in volgorde, zoals ze op de pagina moeten staan.
WAARDEN = {
    "studenten": "1.743",
    "schooljaren": "10",
    "ingeschreven": "564",
    "diplomas": "953",
    "opleidingen": "11",
    "brin": "1",
}
## De drie tegels op Studiesucces (stap "indicatoren").
STUDIESUCCES = {"jaar": "67,9%", "diploma": "68,9%", "starters": "80,7%"}


def leestijd(ondertitel: str) -> float:
    """Seconden in beeld: genoeg om de ondertitel rustig te lezen."""
    return max(3.5, 1.5 + len(ondertitel) / 15)
