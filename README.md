# Staat van de Onderwijsinstelling MBO

Zie in één dashboard hoe het je studenten vergaat: hoeveel er instromen, hoeveel er binnen 3, 5 of 8 jaar een diploma halen, hoeveel er uitvallen en hoeveel er van opleiding wisselen. Je gebruikt alleen de bestanden die je al van DUO krijgt.


## Wat heb je nodig?

- Je **RO-bestanden** (Registratieoverzicht) van DUO. Eén RO beslaat maximaal 2 jaar; met 5 opeenvolgende RO's heb je ongeveer 10 jaar.
- Optioneel je **TBG-i-bestanden**.
- Een computer met Windows of Mac. Je installeert eenmalig drie programma's (hieronder).

## Installeren (één keer)

Open een terminal: op Windows **PowerShell** (zoek in het startmenu), op Mac **Terminal**. Plak de regels één voor één en druk op Enter.

1. **uv** (installeert Python voor je)
   - Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
   - Mac: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. **R**: download en installeer van [cran.r-project.org](https://cran.r-project.org). Kies alle standaardopties.
3. **Het R-pakket staat1cho**: open het programma **R** (staat nu in je startmenu of Programma's), plak deze regel en druk op Enter. Sluit R daarna.
   `install.packages("remotes"); remotes::install_github("cedanl/staat-van-onderwijsinstelling")`
4. **Dit programma**: `uv tool install git+https://github.com/cedanl/staat-van-onderwijsinstelling-mbo`

Sluit daarna de terminal en open een nieuwe.

## Gebruiken

1. Typ in de terminal `smbo dashboard` en druk op Enter. Je browser opent.
2. Klik **Bladeren...**, selecteer al je RO- en TBG-i-bestanden tegelijk en klik **Samenvoegen**.
3. Lees de melding. Staat er **Gelukt**, klik dan **Verder naar het dashboard**.

Sluit de terminal als je klaar bent; dan stopt het dashboard ook.

**Eerst proberen zonder eigen bestanden?** In de map [`demodata`](demodata) staan nep-DUO-bestanden van drie instellingen. Download ze en upload ze in stap 2.

## Zonder scherm (voor automatisering)

```
smbo samenvoegen <bestanden of map> --uitvoer <map>     # maakt 1cho_mbo.csv en meldingen.txt
smbo staat <map>/1cho_mbo.csv --uitvoer <map>           # indicatoren en benchmarkrapport (Excel)
```

Exitcode 0 betekent gelukt. Heb je de bestanden al verwerkt met [mbo-bekostiging-bestanden](https://github.com/cedanl/mbo-bekostiging-bestanden)? Geef dan de map `datamodel` (of de zip) op in plaats van de ruwe bestanden. Dat werkt ook in het dashboard.

## Goed om te weten

- **Alleen je eigen instelling.** Gaat een student naar een andere school, dan telt dat als uitval. Doorstroom naar het hbo is niet te zien.
- **Alle BRIN's die je uploadt tellen als één bestuur.** Een overstap tussen jullie eigen BRIN's is dus geen uitval.
- **Telling op 1 oktober.** Wie alleen tussen twee 1 oktobers ingeschreven was, valt weg.
- **Niet beschikbaar**: vooropleiding, woonplaats en herkomst. Die staan niet in de DUO-bestanden.
- BSN's en onderwijsnummers worden vervangen door een code. Die code is wel terug te rekenen, dus behandel alle uitvoer als persoonsgegevens: houd hem binnen je instelling.
- Laat het benchmarkrapport door je privacy officer toetsen voordat je het deelt.

## Meer weten

[Ontwerp](docs/superpowers/specs/2026-10-14-staat-mbo-design.md) · [Haalbaarheidsonderzoek](https://github.com/cedanl/mbo-bekostiging-bestanden/issues/389) · [Staat van de Onderwijsinstelling (HO)](https://github.com/cedanl/staat-van-onderwijsinstelling) · Licentie: MIT
