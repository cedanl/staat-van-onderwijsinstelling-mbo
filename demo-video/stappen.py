"""Stappen van de demovideo: ondertitel (beeld) en uitspraak (voice-over).

Eén bron voor record.py en generate_audio.py, zodat beeld en geluid gelijk lopen.
De ondertitel is hooguit 110 tekens (tests/test_demo_stappen.py); de uitspraak
spelt afkortingen uit voor de stem.
"""

STAPPEN = [
    (
        "start",
        "Dit is de Staat van de Onderwijsinstelling voor het mbo. Kies je RO-bestanden van DUO.",
        "Dit is de Staat van de Onderwijsinstelling voor het m b o. Hier kies je je R O bestanden van DUO.",
    ),
    (
        "demodata",
        "Nog geen bestanden bij de hand? Probeer de demodata: tien jaar, één verzonnen instelling.",
        "Nog geen bestanden bij de hand? Probeer dan de demodata: tien jaar, van één verzonnen instelling.",
    ),
    (
        "gelukt",
        "Je ziet meteen of het gelukt is en welke meldingen er zijn over je bestanden.",
        "Je ziet meteen of het gelukt is, en welke meldingen er zijn over je bestanden.",
    ),
    (
        "studiesucces",
        "Studiesucces: jaarresultaat, diplomaresultaat en startersresultaat uit de Regeling studiesucces mbo.",
        "Op de pagina Studiesucces zie je het jaarresultaat, het diplomaresultaat en het startersresultaat, volgens de Regeling studiesucces m b o.",
    ),
    (
        "indicatief",
        "Alle cijfers zijn indicatief, geen oordeel: we rekenen de regeling na op jouw bestanden.",
        "Alle cijfers zijn indicatief, en geen oordeel. We rekenen de regeling na op jouw bestanden.",
    ),
    (
        "tabel",
        "Per opleiding zie je de drie cijfers en de norm. Een vernieuwd crebo telt als één opleiding.",
        "Per opleiding zie je de drie cijfers en de norm. Een vernieuwd crebo telt samen met zijn voorganger als één opleiding.",
    ),
    (
        "norm",
        "Per niveau zie je het verloop. De stippellijn is de norm uit de regeling.",
        "Per niveau zie je het verloop over de jaren. De stippellijn is de norm uit de regeling.",
    ),
    (
        "cohorten",
        "Cohorten: hoeveel studenten instromen en welk deel binnen de nominale duur een diploma haalt.",
        "Bij Cohorten zie je hoeveel studenten er instromen, en welk deel binnen de nominale duur een diploma haalt.",
    ),
    (
        "loopbanen",
        "Loopbanen: waar studenten na één, twee of drie jaar staan. Stapelen telt niet als uitval of wissel.",
        "Bij Loopbanen zie je waar studenten na een, twee of drie jaar staan. Stapelen telt niet als uitval of wissel.",
    ),
    (
        "niveaus",
        "Van niveau naar niveau: stapelen na een diploma, opstromen zonder diploma, en afstromen.",
        "Van niveau naar niveau: stapelen na een diploma, opstromen zonder diploma, en afstromen.",
    ),
    (
        "over",
        "Over de cijfers legt de definities uit, noemt de bronnen en toont wat je bestanden dekken.",
        "Over de cijfers legt de definities uit, noemt de bronnen, en laat zien wat je bestanden dekken.",
    ),
    (
        "slot",
        "Zo zie je in een paar klikken hoe het je studenten vergaat.",
        "Zo zie je in een paar klikken hoe het je studenten vergaat.",
    ),
]
