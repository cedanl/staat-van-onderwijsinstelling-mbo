# Staat van de Onderwijsinstelling MBO
<!-- TODO Aslam: nieuwe demovideo slepen -->

Zie in één dashboard hoe het je studenten vergaat: hoeveel er instromen, hoeveel er binnen 3, 5 of 8 jaar een diploma halen, hoeveel er uitvallen en hoeveel er van opleiding wisselen. Je gebruikt alleen de bestanden die je al van DUO krijgt.

Alle cijfers zijn **indicatief, geen oordeel**: ze laten zien hoe de studiesuccescijfers uit de Regeling studiesucces mbo er voor jouw instelling uit zouden zien, maar het zijn niet de cijfers van de Inspectie.


## Wat heb je nodig?

- Je **RO-bestanden** (Registratieoverzicht) van DUO. Eén RO beslaat maximaal 2 jaar; met 5 opeenvolgende RO's heb je ongeveer 10 jaar.
- Optioneel je **TBG-i-bestanden**.
- Een computer met Windows of Mac. Je installeert eenmalig één programma (hieronder).

## Installeren (één keer)

Open een terminal: op Windows **PowerShell** (zoek in het startmenu), op Mac **Terminal**. Plak de regels één voor één en druk op Enter.

1. **uv** (installeert Python voor je)
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Dit programma**: sluit de terminal, open een nieuwe en plak: `uv tool install git+https://github.com/cedanl/staat-van-onderwijsinstelling-mbo`

Sluit daarna de terminal en open een nieuwe.

## Gebruiken

1. Typ in de terminal `smbo dashboard` en druk op Enter. Je browser opent.
2. Klik **Bladeren...**, selecteer al je RO- en TBG-i-bestanden tegelijk en klik **Samenvoegen**.
3. Lees de melding. Staat er **Gelukt**, kies dan links een pagina: Studiesucces, Cohorten, Loopbanen of Over de cijfers.

Sluit de terminal als je klaar bent; dan stopt het dashboard ook.

**Eerst proberen zonder eigen bestanden?** Klik op de startpagina op **Probeer met demodata**. Dat zijn vijf nep-RO-bestanden van één instelling (tien schooljaren, minder dan 2000 verzonnen studenten, met stapelen, op- en afstromen en crebo-vernieuwingen). Je vindt ze ook in [`src/staat_mbo/demodata`](src/staat_mbo/demodata).

## De drie indicatoren

De pagina Studiesucces toont de drie indicatoren uit de [Regeling studiesucces mbo](https://wetten.overheid.nl/BWBR0046913/2022-08-01/0), per jaartijdvak (1 oktober t/m 30 september) en als driejaarscijfer, met de norm uit de regeling als referentielijn:

- **Jaarresultaat**: van de studenten die een diploma haalden of de instelling zonder diploma verlieten, het deel met een diploma.
- **Diplomaresultaat**: van de studenten die de instelling verlaten, het deel met een diploma op niveau 2, 3 of 4 uit het jaartijdvak of de vijf jaar ervoor.
- **Startersresultaat**: van de nieuwe studenten het deel dat een jaar later nog op niveau 2, 3 of 4 is ingeschreven of een diploma haalde.

Een vernieuwd crebo telt samen met zijn voorganger als één opleiding. Onder de 12 studenten tonen we geen percentage. De pagina **Over de cijfers** legt de definities, de bronnen en wat je met je bestanden kunt berekenen uit.

## Zonder scherm (voor automatisering)

```
smbo samenvoegen <bestanden of map> --uitvoer <map>     # tussenlaag (parquet) en meldingen.txt
smbo staat <bestanden of map> --uitvoer <map>           # studiesucces.csv, cohorten.csv en loopbanen.csv
```

Exitcode 0 betekent gelukt. Heb je de bestanden al verwerkt met [mbo-bekostiging-bestanden](https://github.com/cedanl/mbo-bekostiging-bestanden)? Geef dan de map `datamodel` (of de zip) op in plaats van de ruwe bestanden. Dat werkt ook in het dashboard.

## Goed om te weten

- **Indicatief, geen oordeel.** We rekenen de regeling na op jouw bestanden. Dat is geen inspectieoordeel en kan afwijken van de cijfers van de Inspectie.
- **Alleen je eigen instelling.** Gaat een student naar een andere school, dan telt dat als uitval. Doorstroom naar het hbo is niet te zien.
- **Alle BRIN's die je uploadt tellen als één bestuur.** Een overstap tussen jullie eigen BRIN's is dus geen uitval.
- **Telling op 1 oktober.** Wie alleen tussen twee 1 oktobers ingeschreven was, valt weg.
- **Genoeg historie nodig.** Met minder dan zes jaar zijn het diplomaresultaat en het startersresultaat nog onvolledig; het dashboard meldt dat.
- **Niet beschikbaar**: vooropleiding, woonplaats en herkomst. Die staan niet in de DUO-bestanden.
- BSN's en onderwijsnummers worden vervangen door een code. Die code is wel terug te rekenen, dus behandel alle uitvoer als persoonsgegevens: houd hem binnen je instelling.
- Laat de uitvoer door je privacy officer toetsen voordat je hem deelt.

## Meer weten

[Ontwerp](docs/superpowers/specs/2026-11-04-mbo-dashboard-design.md) · [Haalbaarheidsonderzoek](https://github.com/cedanl/mbo-bekostiging-bestanden/issues/389) · [Staat van de Onderwijsinstelling (HO)](https://github.com/cedanl/staat-van-onderwijsinstelling) · Licentie: MIT
