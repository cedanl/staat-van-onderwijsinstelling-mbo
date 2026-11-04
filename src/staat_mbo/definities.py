"""Teksten over de cijfers, op één plek: voor ``help=`` en de pagina Over de cijfers."""

from staat_mbo import palet

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
        "1 jaar, na de nominale duur van de opleiding of een jaar daarna, in "
        "negen vaste categorieën."
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

## Vaste kleuren per categorie (Npuls-palet, zie palet.py), in dezelfde volgorde.
CATEGORIE_KLEUREN = palet.CATEGORIE_KLEUREN

NAMEN = {
    "jr": "Jaarresultaat",
    "dr": "Diplomaresultaat",
    "sr": "Startersresultaat",
    "driejaarscijfer": "Driejaarscijfer en norm",
    "instroomcohort": "Instroomcohort",
    "rendement_nominaal": "Rendement nominaal",
    "rendement_nominaal_plus_1": "Rendement nominaal + 1",
    "uitval": "Uitval",
    "loopbaanstatus": "Loopbaanstatus",
    "studiewissel": "Studiewissel",
}

## Bronnen: naam en link.
BRONNEN = {
    "Regeling studiesucces mbo (Stcrt. 2022, 18467)": (
        "https://zoek.officielebekendmakingen.nl/stcrt-2022-18467.pdf"
    ),
    "Uitvoeringsbesluit WEB, hoofdstuk 4A (Stb. 2022, 273)": (
        "https://zoek.officielebekendmakingen.nl/stb-2022-273.pdf"
    ),
    "Regeling studiesucces mbo op wetten.overheid.nl": (
        "https://wetten.overheid.nl/BWBR0046913/2022-08-01/0"
    ),
    "DUO, toelichting berekende indicatoren mbo 2024": (
        "https://duo.nl/open_onderwijsdata/images/2024-toelichting-berekende-indicatoren.pdf"
    ),
}

## Waarin deze cijfers verschillen van die van de Inspectie en van v4.
VERSCHILLEN = [
    (
        "De Inspectie rekent op het register (ROD); wij rekenen op je eigen RO's. "
        "Verwacht een verschil van enkele procentpunten."
    ),
    (
        "Alle bestanden die je uploadt tellen als één instelling (bestuur). Een "
        "overstap tussen je eigen BRIN's maakt iemand geen instellingsverlater."
    ),
    (
        "Per student en 1 oktober telt één inschrijving: het hoogste niveau, dan het "
        "laagste crebo, dan de recentste start. Welke de Inspectie kiest, staat niet "
        "in de regeling."
    ),
    (
        "Een opleiding is een crebo; een crebo-vernieuwing telt samen via de opvolger "
        "in de opleidingstabel, waar die is gevuld."
    ),
    "OVO en ODT vallen buiten de cijfers, entree (niveau 1) ook. Extranei tellen mee.",
    "We filteren niet op bekostigbaarheid van de student.",
    (
        "Onder een noemer van 12 tonen we geen percentage. Die grens komt uit het "
        "document van de Inspectie dat mbo-bekostiging-bestanden noemt; we hebben "
        "het niet kunnen nalezen."
    ),
    (
        "Het jaarresultaat en diplomaresultaat in mbo-bekostiging-bestanden zijn een "
        "benadering (schooljaar in plaats van jaartijdvak, een andere noemer voor het "
        "jaarresultaat). Deze app volgt de regeling; daardoor verschillen de cijfers."
    ),
    (
        "We tonen de norm uit de regeling als referentielijn. We berekenen geen "
        "oordeel: niet de 2-van-3-regel en geen maatwerk."
    ),
]
