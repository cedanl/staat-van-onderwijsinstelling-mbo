"""Stappen van de demovideo: ondertitel (beeld), uitspraak (voice-over) en chip.

Eén bron voor record.py, generate_audio.py en stitch.py, zodat beeld en geluid
gelijk lopen. De ondertitel is hooguit 110 tekens (tests/test_demo_stappen.py);
de uitspraak spelt afkortingen en getallen uit voor de stem.

CHIPS: per stap (label, toelichting, kleur) voor het kader met pijl in de app.
WAARDEN: de kerncijfers zoals ze op de pagina moeten staan; record.py controleert
ze tegen het scherm, zodat tekst en beeld kloppen.
"""

STAPPEN = [
    (
        "start",
        "Het dashboard rekent het studiesucces van je instelling na, op basis van je eigen RO-bestanden.",
        "Dit is de Staat van de Onderwijsinstelling voor het m b o. Het rekent je studiesucces na, op je eigen R O bestanden.",
    ),
    (
        "privacy",
        "Je bestanden blijven op je eigen computer en persoonsnummers krijgen een code.",
        "Je bestanden blijven op je eigen computer. Persoonsnummers krijgen een code.",
    ),
    (
        "kies",
        "Kies met de bestandskiezer al je RO-bestanden tegelijk: hier vijf bestanden over tien jaar.",
        "Kies hier je R O bestanden, alle vijf tegelijk.",
    ),
    (
        "samenvoegen",
        "Klik op Samenvoegen: de bestanden worden gecontroleerd en tot één geheel gemaakt.",
        "Klik op Samenvoegen, dan worden ze gecontroleerd.",
    ),
    (
        "gelukt",
        "Gelukt: je ziet voor welke instelling, welke schooljaren en hoeveel studenten het geldt.",
        "Gelukt. Je ziet de instelling, de schooljaren en het aantal studenten.",
    ),
    (
        "meldingen",
        "Meldingen vertellen wat er aan je bestanden opvalt, zoals een cohort dat nog te kort loopt.",
        "Meldingen vertellen wat opvalt, bijvoorbeeld een cohort dat nog te kort loopt.",
    ),
    (
        "jaar",
        "Jaarresultaat 67,9%: een driejaarscijfer over 2022-23 t/m 2024-25.",
        "De kerncijfers. Het jaarresultaat is zevenenzestig komma negen procent, over de laatste drie jaar.",
    ),
    (
        "diploma",
        "Diplomaresultaat 68,9%, over dezelfde drie jaar.",
        "Het diplomaresultaat is achtenzestig komma negen procent.",
    ),
    (
        "starters",
        "Startersresultaat 80,7%, over dezelfde drie jaar.",
        "Het startersresultaat is tachtig komma zeven procent.",
    ),
    (
        "instroom",
        "Instroom: 226 nieuwe studenten in het laatste cohort, 2025.",
        "De instroom is tweehonderdzesentwintig studenten.",
    ),
    (
        "uitval",
        "Uitval na 1 jaar: 16,4% van cohort 2024 is een jaar later weg zonder diploma.",
        "Zestien komma vier procent valt na één jaar uit.",
    ),
    (
        "doorstroom",
        "Doorstroom na diploma: 22,5% van de gediplomeerden gaat binnen drie jaar verder op een hoger niveau.",
        "En tweeëntwintig komma vijf procent van de gediplomeerden stapelt door naar een hoger niveau.",
    ),
    (
        "indicatoren",
        "Jaarresultaat, diplomaresultaat en startersresultaat: de drie cijfers uit de Regeling studiesucces mbo.",
        "Studiesucces volgt de Regeling studiesucces m b o. Jaarresultaat: van wie vertrekt, wie slaagt. Diplomaresultaat: van wie vertrekt, wie een diploma heeft. Startersresultaat: van nieuwe studenten, wie een jaar later nog studeert of slaagt.",
    ),
    (
        "tabel",
        "Per opleiding zie je de cijfers en de norm. Bij minder dan 12 studenten staat geen percentage.",
        "Per opleiding zie je de cijfers en de norm. Bij minder dan twaalf studenten staat geen percentage.",
    ),
    (
        "norm",
        "Per niveau zie je het verloop. De stippellijn is de neutrale norm uit de regeling, geen oordeel.",
        "De stippellijn is de neutrale norm per niveau. Geen oordeel.",
    ),
    (
        "filter",
        "Met de filters links kijk je naar één niveau, leerweg, domein of opleiding.",
        "Filter op één niveau of opleiding.",
    ),
    (
        "gefilterd",
        "Hier alleen niveau 4: de cijfers veranderen mee.",
        "Hier alleen niveau vier.",
    ),
    (
        "instroomcohort",
        "Cohorten: hoeveel studenten instromen, en waar ze vandaan komen.",
        "Cohorten: de instroom, naar herkomst.",
    ),
    (
        "rendement",
        "Rendement nominaal en nominaal + 1. Grijs betekent: nog niet waarneembaar.",
        "Rendement nominaal en nominaal plus één. Grijs is nog niet waarneembaar.",
    ),
    (
        "uitvalcohort",
        "Uitval per cohort, na 1 jaar en na de nominale duur.",
        "En de uitval per cohort.",
    ),
    (
        "loopbanen",
        "Loopbanen: waar studenten na 1, 2 of 3 jaar staan. Stapelen telt niet als uitval of wissel.",
        "Loopbanen: waar studenten na één, twee of drie jaar staan. Stapelen telt niet als uitval.",
    ),
    (
        "niveaus",
        "Stapelen, opstromen en afstromen: dit onderscheidt het mbo.",
        "Stapelen, opstromen en afstromen: dit onderscheidt het m b o.",
    ),
    (
        "over",
        "Over de cijfers legt de definities uit, noemt de bronnen en toont wat je bestanden dekken.",
        "Over de cijfers: definities, bronnen en dekking.",
    ),
    (
        "indicatief",
        "Indicatief: berekend op je eigen RO's, niet op het register van de Inspectie. Geen oordeel.",
        "Alles is indicatief, berekend op je eigen R O's en niet op het register van de Inspectie. Geen oordeel.",
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
    "jaar": ("Jaarresultaat", "Driejaarscijfer 2022-23 t/m 2024-25.", "blauw"),
    "diploma": ("Diplomaresultaat", "Zelfde drie jaar.", "blauw"),
    "starters": ("Startersresultaat", "Zelfde drie jaar.", "blauw"),
    "instroom": ("Instroom", "Nieuwe studenten in cohort 2025.", "blauw"),
    "uitval": (
        "Uitval na 1 jaar",
        "Cohort 2024, een jaar later weg zonder diploma.",
        "oranje",
    ),
    "doorstroom": (
        "Doorstroom na diploma",
        "Van de gediplomeerden, na drie jaar (cohort 2022).",
        "groen",
    ),
    "indicatoren": (
        "Regeling studiesucces",
        "Drie indicatoren, elk met een eigen vraag.",
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

## Kerncijfers zoals ze op Start staan; record.py controleert ze tegen het scherm.
WAARDEN = {
    "jaar": "67,9%",
    "diploma": "68,9%",
    "starters": "80,7%",
    "instroom": "226",
    "uitval": "16,4%",
    "doorstroom": "22,5%",
}
