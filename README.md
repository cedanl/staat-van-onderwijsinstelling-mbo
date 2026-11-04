# Staat van de Onderwijsinstelling MBO
<!-- TODO Aslam: nieuwe demovideo slepen -->

Zie in één dashboard hoe het je studenten vergaat. Je ziet het studiesucces volgens de Regeling studiesucces mbo, hoeveel studenten instromen en binnen de nominale duur een diploma halen, en wie stapelt, op- of afstroomt, wisselt of uitvalt. Je gebruikt alleen de bestanden die je al van DUO krijgt. Ze blijven op je eigen computer.

Alle cijfers zijn **indicatief, geen oordeel**. Ze laten zien hoe de studiesuccescijfers voor jouw instelling uit zouden vallen, maar het zijn niet de cijfers van de Inspectie.

## Wat heb je nodig?

- Je **RO-bestanden** (Registratieoverzicht) van DUO. Eén RO beslaat maximaal 2 jaar; met 5 opeenvolgende RO's heb je ongeveer 10 jaar. Hoe meer jaren, hoe meer cijfers volledig zijn (zie [Genoeg historie](#goed-om-te-weten)).
- Optioneel je **TBG-i-bestanden**. Alleen TBG-i is niet genoeg: er moet minstens één RO bij.
- Een computer met Windows of Mac. Je installeert eenmalig één programma (hieronder).

## Installeren (één keer)

Open een terminal: op Windows **PowerShell** (zoek in het startmenu), op Mac **Terminal**. Plak de regels één voor één en druk op Enter.

1. **uv** (installeert Python voor je)
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **Dit programma**: sluit de terminal, open een nieuwe en plak: `uv tool install git+https://github.com/cedanl/staat-van-onderwijsinstelling-mbo`

Sluit daarna de terminal en open een nieuwe.

**Bijwerken naar de nieuwste versie:** `uv tool upgrade staat-mbo`

## Gebruiken

1. Typ in de terminal `smbo dashboard` en druk op Enter. Je browser opent.
2. Sleep al je RO- en TBG-i-bestanden tegelijk in het vak (of klik **Browse files**) en klik **Samenvoegen**.
3. Lees de meldingen. Staat er **Gelukt**, kies dan links een pagina.

Sluit de terminal als je klaar bent; dan stopt het dashboard ook. Geeft `smbo dashboard` een fout dat de poort bezet is, dan draait het dashboard al ergens: sluit die andere terminal, of start met `smbo dashboard --poort 8502`.

**Eerst proberen zonder eigen bestanden?** Klik op de startpagina op **Probeer met demodata**. Dat zijn vijf nep-RO-bestanden van één kleine instelling: tien schooljaren, minder dan 2000 verzonnen studenten, met stapelen, op- en afstromen en crebo-vernieuwingen. Je vindt ze ook in [`src/staat_mbo/demodata`](src/staat_mbo/demodata). De demodata zijn verzonnen en lijken inhoudelijk niet op een echte instelling.

## De pagina's

- **Start**: bestanden kiezen en samenvoegen, de meldingen, en tellingen over je bestanden: studenten, schooljaren, ingeschreven op de laatste 1 oktober, diploma's, opleidingen en BRIN-nummers.
- **Studiesucces**: de drie indicatoren uit de regeling (hieronder), voor de instelling, per niveau en per opleiding, met de norm als referentielijn.
- **Cohorten**: per instroomcohort de instroom (nieuw, na een diploma, van een ander niveau of na een wissel), het rendement binnen de nominale duur en een jaar later, en de uitval na 1 jaar en na de nominale duur. Grijs betekent: nog niet te zien, het cohort loopt nog.
- **Loopbanen**: waar studenten staan na 1 jaar, na de nominale duur van hun opleiding en een jaar later. Bijvoorbeeld met een diploma verder op een hoger niveau, zonder diploma opgestroomd of afgestroomd, of uitgevallen. Plus een tabel van niveau naar niveau.
- **Over de cijfers**: definities, bronnen, de verschillen met de Inspectie en wat je bestanden dekken.

Met de filters links (niveau, leerweg, domein, opleiding) kijk je naar een deel; ze gelden op alle pagina's. Tabellen kun je downloaden als CSV.

## De drie indicatoren

De pagina Studiesucces toont de drie indicatoren uit de [Regeling studiesucces mbo](https://wetten.overheid.nl/BWBR0046913/2022-08-01/0). Ze worden berekend per jaartijdvak (1 oktober t/m 30 september) en als driejaarscijfer:

- **Jaarresultaat**: van de studenten die een diploma haalden of de instelling zonder diploma verlieten, het deel met een diploma.
- **Diplomaresultaat**: van de studenten die de instelling verlaten, het deel met een diploma op niveau 2, 3 of 4 uit het jaartijdvak of de vijf jaar ervoor.
- **Startersresultaat**: van de nieuwe studenten het deel dat een jaar later nog op niveau 2, 3 of 4 is ingeschreven of een diploma haalde.

Een vernieuwd crebo telt samen met zijn voorganger als één opleiding. Onder de 12 studenten tonen we geen percentage.

## Als het niet lukt

Na **Samenvoegen** zie je **Gelukt** of **Niet gelukt**, met de reden. De meest voorkomende:

- **De kwaliteitscontrole keurt een bestand af.** De melding noemt het bestand en de reden, bijvoorbeeld dat de aantallen in de laatste regel (SLR) niet kloppen. Meestal is het bestand bewerkt of niet helemaal gedownload. Vraag dan een nieuwe RO aan bij DUO.
- **Onbekend bestand.** De naam moet beginnen met `RO_` of `TBGI_`, zoals DUO hem levert. Hernoem de bestanden niet.
- **Het datamodel is niet compleet of te oud.** Maak het datamodel opnieuw met de nieuwste versie van mbo-bekostiging-bestanden, of upload de ruwe RO's.
- **Let op: een BRIN begint later of houdt eerder op.** Bij meerdere BRIN's rekenen we alleen over de 1 oktobers die alle BRIN's dekken. Eén BRIN met een korte reeks maakt dus alles kort. Upload voor elke BRIN dezelfde jaren, of laat die BRIN weg.

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
