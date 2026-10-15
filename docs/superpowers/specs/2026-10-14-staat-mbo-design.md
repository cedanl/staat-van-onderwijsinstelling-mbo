# Staat van de Onderwijsinstelling MBO — ontwerp

Pitch: [#1](https://github.com/cedanl/staat-van-onderwijsinstelling-mbo/issues/1). Onderzoek: cedanl/mbo-bekostiging-bestanden#389.

## Doel

Een mbo-instelling krijgt dezelfde ervaring als het HO met `staat1cho`: één pagina, bestanden uploaden, klikken, dashboard. Dezelfde stappen werken ook zonder scherm (commandoregel, bijv. in een cronjob).

## Gebruikerservaring

1. **Uploaden.** Eén pagina. De gebruiker uploadt óf de ruwe RO- en TBG-i-bestanden, óf de uitvoer van `mbo-bekostiging-bestanden` (de `datamodel/`-parquetbestanden, los of als zip).
2. **Samenvoegen.** Knop "Samenvoegen". De app maakt er één 1CHO-bestand van en meldt het resultaat: gedekte schooljaren en BRIN's, aantal studenten, gaten tussen leveringen, fouten. Bij een fout kan de gebruiker niet verder.
3. **Dashboard.** Knop "Verder": het bestaande `staat1cho`-dashboard op dat bestand.

## Opbouw

**Deze repo: Python-pakket `staat-mbo`** (Python ≥ 3.13, polars, uv). Hangt af van `mbo-bekostiging-bestanden` (vastgepinde tag) en gebruikt diens functies; geen eigen inleeslogica.

| Module | Taak |
|---|---|
| `bron.py` | Ruwe bestanden door de pipeline van `mbo-bekostiging-bestanden` (verwerken + `run_star`), of een bestaande `datamodel/` inlezen |
| `stapelcontrole.py` | Dekking per BRIN en schooljaar, gaten tussen leveringen |
| `naar_1cho.py` | Star → 1CHO-vorm volgens de vertaaltabel in de pitch; één functie per regel |
| `cli.py` | Commando `smbo` |

Commando's:

- `smbo samenvoegen <bestanden of datamodel-map> --uitvoer <map>` → `1cho_mbo.csv` + `stapelcontrole.json`. Exitcode ≠ 0 bij fouten. Dit is ook de stap die het dashboard aanroept.
- `smbo staat <1cho_mbo.csv> --uitvoer <map>` → indicatoren en benchmarkrapport via `Rscript` met `staat1cho` (zonder scherm).
- `smbo dashboard` → start het dashboard met de mbo-voorstap.

**`staat1cho`: één PR in `staat-van-onderwijsinstelling`.**

- `start_dashboard(voorstap = NULL)`: optionele eerste stap "bronbestanden uploaden → samenvoegen → resultaat tonen". Zonder `voorstap` blijft het HO-dashboard ongewijzigd.
- `maak_diploma_behaald(..., diplomasoorten = )` instelbaar; standaard de huidige hbo/wo-lijst.

`smbo dashboard` start `staat1cho::start_dashboard()` met een voorstap die `smbo samenvoegen` aanroept en mbo-diplomasoorten meegeeft.

## Regels

- Alle aangeleverde BRIN's tellen als één bestuur; de melding toont welke BRIN's zijn samengevoegd.
- Overlap tussen leveringen: de meest recente telt (canonicalisatie van `mbo-bekostiging-bestanden`).
- Kolommen zonder mbo-bron blijven leeg.

## Testen

- pytest per vertaalregel met kleine handgemaakte tabellen.
- End-to-end op de demodata van `mbo-bekostiging-bestanden`: ruw → `samenvoegen` → `staat`. De R-stap wordt overgeslagen als R ontbreekt.
- Test dat de `datamodel/`-uitvoer van `mbo-bekostiging-bestanden` direct als invoer werkt.

## README

Kort: wat het is, installeren (uv + R + `staat1cho`), de drie schermen, de commando's, beperkingen in één lijstje. Schrijf voor iemand die nog nooit een terminal heeft geopend.

Bovenaan een demovideo met Nederlandse voice-over: uploaden → samenvoegen → dashboard doorklikken. Gemaakt met de `demo-video`-skill uit `cedanl/.github` (Playwright, piper-tts, FFmpeg) op de demodata van `mbo-bekostiging-bestanden`; via github.com in de README gezet (sleep de video in de editor), niet in git. Het opnamescript staat in de repo, zodat de video opnieuw te maken is als de app verandert.

## Buiten scope

GRONDSLAG, benchmark tussen instellingen, kansengelijkheid, mapping BRIN → bestuur, de toets op echte data (doet de gebruiker).

## Pseudonimiseren

Ingebouwde vaste sleutel (`bron.INGEBOUWDE_SLEUTEL`): gebruikers stellen niets in en elke run geeft dezelfde pseudoniemen. Een eigen sleutel via `MBO_PSEUDONIMISERING_SALT` gaat voor. Uitvoer blijft persoonsgegevens.
