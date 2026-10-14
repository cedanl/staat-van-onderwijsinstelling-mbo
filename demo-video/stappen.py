"""Stappen van de demovideo: ondertitel (beeld) en uitspraak (voice-over).

Eén bron voor record.py en generate_audio.py, zodat beeld en geluid gelijk lopen.
"""

STAPPEN = [
    ("intro", "Dit is de Staat van de Onderwijsinstelling voor het mbo. Alles gebeurt op deze ene pagina.",
     "Dit is de Staat van de Onderwijsinstelling voor het m b o. Alles gebeurt op deze ene pagina."),
    ("bestanden", "Klik op Bladeren en kies al je RO- en TBG-i-bestanden van DUO tegelijk.",
     "Klik op Bladeren, en kies al je R O en T B G i bestanden van DUO tegelijk."),
    ("samenvoegen", "Klik op Samenvoegen. De bestanden worden één bestand.",
     "Klik op Samenvoegen. De bestanden worden samengevoegd tot één bestand."),
    ("gelukt", "Je ziet meteen of het gelukt is: welke jaren, hoeveel studenten en waar je op moet letten.",
     "Je ziet meteen of het gelukt is. Welke instellingen en schooljaren erin zitten, hoeveel studenten, en waar je op moet letten."),
    ("verder", "Gelukt? Klik op Verder naar het dashboard.",
     "Is het gelukt? Klik dan op Verder naar het dashboard."),
    ("tabs", "Bovenaan staan de onderdelen: instroom, rendement, uitval en studiewissel.",
     "Dit is het dashboard. Bovenaan staan de onderdelen: instroom, rendement, uitval en studiewissel."),
    ("rendement", "Rendement: hoeveel studenten binnen 3, 5 of 8 jaar een diploma halen.",
     "Onder Rendement zie je hoeveel studenten binnen drie, vijf of acht jaar een diploma halen."),
    ("uitval", "Uitval: hoeveel studenten zonder diploma vertrekken.",
     "Onder Uitval zie je hoeveel studenten zonder diploma vertrekken."),
    ("filter", "Links filter je, bijvoorbeeld op BOL of BBL. De cijfers passen zich direct aan.",
     "Links kun je filteren, bijvoorbeeld op B O L of B B L. Alle cijfers passen zich direct aan."),
    ("slot", "Met Nieuw bestand begin je opnieuw.",
     "Met Nieuw bestand begin je opnieuw. Zo zie je in een paar klikken hoe het je studenten vergaat."),
]
