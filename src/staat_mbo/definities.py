"""Teksten over de cijfers, op één plek: voor ``help=`` en de pagina Over de cijfers."""

## Het label dat op elke pagina met cijfers staat (ontwerp §3).
LABEL = (
    "Indicatief: berekend op je eigen RO's, niet op het register (ROD) waarmee "
    "de Inspectie rekent. Geen oordeel."
)
## De norm is een neutrale referentielijn, geen beoordeling.
NORM_LABEL = "norm Regeling studiesucces mbo"

DEFINITIES = {
    "jr": (
        "Jaarresultaat: van de studenten die in het jaartijdvak (1 oktober t/m "
        "30 september) een diploma op niveau 2, 3 of 4 haalden of de instelling "
        "zonder diploma verlieten, het deel dat een diploma haalde. Wie "
        "ingeschreven blijft zonder diploma, telt niet mee."
    ),
    "dr": (
        "Diplomaresultaat: van de studenten die de instelling verlaten (op 1 "
        "oktober ingeschreven, een jaar later niet meer), het deel met een "
        "diploma op niveau 2, 3 of 4 uit het jaartijdvak of de vijf jaar ervoor. "
        "Een eerder diploma op een lager niveau telt mee."
    ),
    "sr": (
        "Startersresultaat: van de nieuw ingeschreven studenten (op geen van de "
        "zes voorgaande 1 oktobers ingeschreven), het deel dat een jaar later "
        "nog op niveau 2, 3 of 4 is ingeschreven of in het jaartijdvak een "
        "diploma haalde. Opstromen en wisselen binnen de instelling blijven "
        "positief, afstromen naar entree niet."
    ),
    "driejaarscijfer": (
        "Driejaarscijfer: de tellers en noemers van de laatste drie jaartijdvakken "
        "worden opgeteld en gedeeld (regeling art. 4, lid 2). Het cijfer is er "
        "alleen als alle drie de jaren waarneembaar zijn. Onder een noemer van "
        "12 tonen we geen percentage."
    ),
    "instroomcohort": (
        "Instroomcohort: studenten die in een jaar voor het eerst op 1 oktober "
        "bij een crebo en leerweg staan, waarvan de opleiding in dat jaar "
        "begon. Een crebo-vernieuwing telt als dezelfde opleiding. Wie al "
        "eerder begon dan we kunnen waarnemen, valt erbuiten."
    ),
    "rendement_nominaal": (
        "Rendement nominaal: het deel van een instroomcohort met een diploma op "
        "minstens het instroomniveau, uiterlijk op 30 september van het jaar "
        "waarin de nominale studieduur eindigt."
    ),
    "rendement_nominaal_plus_1": (
        "Rendement nominaal + 1: als nominaal, maar met een jaar extra."
    ),
    "uitval": (
        "Uitval: niet meer ingeschreven op 1 oktober na 1 jaar (of na de "
        "nominale duur) en sinds de start geen mbo-diploma. Het is een status op "
        "dat moment: wie terugkomt, is op dat moment niet uitgevallen."
    ),
    "loopbaanstatus": (
        "Loopbaanstatus: waar een student van het cohort staat op 1 oktober na "
        "1, 2 of 3 jaar, in negen vaste categorieën."
    ),
    "studiewissel": (
        "Studiewissel: zonder diploma naar een ander crebo op hetzelfde niveau. "
        "Stapelen (na een diploma verder op een hoger niveau) en op- of "
        "afstromen tellen niet als wissel."
    ),
}

## Wat elke loopbaanstatus betekent, per categorie van ``cohorten.CATEGORIEEN``.
CATEGORIE_TOELICHTING = {
    "Diploma, verder op hoger niveau": (
        "Stapelen: diploma gehaald en een jaar later ingeschreven op een hoger "
        "niveau. Telt niet als uitval of wissel."
    ),
    "Diploma, vertrokken": (
        "Diploma gehaald en een jaar later niet meer bij de instelling."
    ),
    "Diploma, nog ingeschreven op hetzelfde of lager niveau": (
        "Diploma gehaald en toch weer ingeschreven op hetzelfde of een lager niveau."
    ),
    "Zonder diploma, zelfde opleiding": (
        "Nog bezig: nog ingeschreven voor hetzelfde crebo (of zijn opvolger)."
    ),
    "Zonder diploma, ander crebo op hetzelfde niveau": (
        "Studiewissel: zonder diploma naar een ander crebo op hetzelfde niveau."
    ),
    "Zonder diploma, hoger niveau": "Opstromen: zonder diploma naar een hoger niveau.",
    "Zonder diploma, lager niveau": (
        "Afstromen: zonder diploma naar een lager niveau, entree inbegrepen."
    ),
    "Vertrokken zonder diploma": (
        "Uitgevallen: niet meer ingeschreven en sinds de start geen diploma."
    ),
    "Nog niet waarneembaar": (
        "Het moment na de start valt nog niet in je bestanden. Dit is geen uitkomst."
    ),
}

## Vaste kleuren per categorie, in dezelfde volgorde: diploma's blauw,
## zonder diploma warm, uitval grijs. Geen rood of groen: het is geen oordeel.
CATEGORIE_KLEUREN = [
    "#1f4e79",
    "#4c78a8",
    "#9ecae1",
    "#f2b134",
    "#f58518",
    "#b279a2",
    "#9d7660",
    "#6b6b6b",
    "#d0d4d9",
]
