# Uitvoeringsplan: mbo-dashboard in Python (issue #6)

Ontwerp: `spec.md` (dit plan verwijst naar paragrafen als §5.1 enz.).

## Werkwijze voor elke taak
- **Tests eerst** (superpowers:test-driven-development). Schrijf de genoemde tests, zie ze falen, bouw en zie ze slagen.
- Stack: Python ≥ 3.13, polars, uv, ruff (`line-length = 88`). Draaien: `uv run pytest -q` en `uv run ruff check . && uv run ruff format --check .`.
- Testconventies van de repo:
  - pytest-functies `test_<gedrag>` in het Nederlands.
  - Kleine in-memory polars-frames.
  - Helper `_waarde(expr, **kolommen)` voor expressies.
  - Fixtures in `tests/conftest.py`; `demo_star` (sessie) voor de nep-RO's in `tests/fixtures/ruw`.
- Code en commentaar in het Nederlands, docstrings kort, `##`-commentaar voor constanten (repo-stijl).
- Bestaande CRLF/LF-regeleinden per bestand behouden (zie commits `5c16358` en `e18e579`).
- Eén commit per taak, met de conventionele prefix (`feat:`, `fix:`, `docs:`, `chore:`) en het attributieregel uit de systeemreminder.
- Klaar = de tests van de taak slagen, de hele suite slaagt en ruff is schoon.

## Volgorde en parallelliteit

```
T0 ─┬─ T1 (waarneming) ─┬──────────────┬─ T5 JR ─┐
    ├─ T2 (peilmomenten)┤              ├─ T6 DR ─┼─ T8 driejaarscijfer ─┐
    ├─ T3 (diplomas) ───┤              ├─ T7 SR ─┘                      │
    └─ T4 (duur) ───────┤              ├─ T9 cohorten ─┬─ T10 rendement ┤
                        │              │               └─ T11 uitval+loopbaan
                        └─ T12 historie┘                                │
                                                     T13 analyse+CLI staat ─ T14 app+start ─┬─ T15 studiesucces
                                                                                           ├─ T16 cohorten
                                                                                           ├─ T17 loopbanen
                                                                                           └─ T18 over
                                                                     T19 dashboard-cmd + R/1CHO eruit
                                                                     T20 toets echte data (Aslam)
                                                                     T21 demodata → T22 README → T23 demovideo → T24 wiki
```

- **Parallel na T0:** T1, T2, T3, T4.
- **Parallel na T1–T3:** T5, T6, T7, T8 (T8 werkt op een generiek teller/noemer-frame), T9, T12.
- **Parallel na T9 (en T4):** T10 en T11.
- **Parallel na T14:** T15, T16, T17, T18.
- **Daarna strikt na elkaar:** T19 → T20 → T21 → T22 → T23 → T24.

---

## T0. Branch, afhankelijkheid en testhelpers
- **Doel:** een werkplek en gedeelde bouwers voor testdata.
- **Bestanden:** `pyproject.toml`, `uv.lock`, `tests/maak.py` (nieuw), `tests/test_maak.py` (nieuw).
- **Eerst:** vraag Aslam (open vraag 6) of de nieuwe branch `feat/dashboard-python` van `c7645e6` mag vertrekken. Doe niets zonder dat antwoord.
- **Tests eerst** (`tests/test_maak.py`):
  - `peilmomenten([("s1", 2022, "25498", 2, "BOL")])` geeft 1 rij met het schema uit spec §4 (`_persoon_id` str, `Jaar` i32, `BRIN` "27DV" standaard, `Inschrijvingvolgnummer` "1", `Opleidingcode`, `Niveau` i32, `Leertraject`, `DatumBegin` = 1-8-Jaar standaard).
  - `diplomas([("s1", "25498", 2, date(2023, 6, 30))])` geeft `Jaartijdvak == 2022`, `Leertraject` "BOL" standaard, `BRIN` "27DV".
  - `waarneming(2018, 2025)` geeft een `Waarneming` met `eerste_jaar=2018`, `laatste_jaar=2025`, `gaten=[]` en `diplomas_vanaf=date(2018, 8, 1)`. Dit hangt af van T1: maak het helperdeel af nadat T1 de dataclass heeft, of definieer de dataclass hier en laat T1 de bouwfunctie leveren. Kies het laatste.
- **Stappen:**
  1. `streamlit>=1.40` toevoegen aan `dependencies` en `uv lock` draaien.
  2. Dataclass `Waarneming` in `src/staat_mbo/waarneming.py`, alleen de velden en `waarneembaar`/`reeks` (zie T1-tests).
  3. Bouwers in `tests/maak.py`.
- **Klaar:** `uv run pytest -q` groen, `streamlit` te importeren.

## T1. Waarneming uit `meta_leveringen`
- **Doel:** bepalen welke 1 oktobers betrouwbaar zijn (spec §4).
- **Bestanden:** `src/staat_mbo/waarneming.py`, `tests/test_waarneming.py`.
- **Tests eerst:**
  - Eén BRIN, RO's 1-8-2020 t/m 31-7-2026, `Laatste_peildatum` 2025-10-01 → `eerste_jaar=2020`, `laatste_jaar=2025`, `diplomas_vanaf=2020-08-01`.
  - Twee BRIN's: A tot `Laatste_peildatum` 2025-10-01, B tot 2024-10-01 → `laatste_jaar=2024` (het vroegste einde).
  - Twee BRIN's: A vanaf 2018-08-01, B vanaf 2020-08-01 → `eerste_jaar=2020`.
  - Gat: RO A 2020-08-01..2022-07-31 en 2023-08-01..2025-07-31 → `gaten` bevat 2022 (1-10-2022 ligt in het gat). `waarneembaar(2022) is False`, `reeks(2021, 2023) is False`, `reeks(2023, 2024) is True`.
  - Een levering zonder `DatumBeginPeriode` (TBG-i) telt niet mee voor `eerste_jaar`.
  - `waarneembaar(2019) is False` bij `eerste_jaar=2020`.
- **Stappen:** `waarneming(star) -> Waarneming`, met hergebruik van `stapelcontrole._gaten` (maak die publiek als `gaten`, en houd de oude naam als alias tot T19).
- **Afhankelijk van:** T0.
- **Klaar:** tests groen; ook `waarneming(demo_star)` werkt (smoke-test met de `demo_star`-fixture: `eerste_jaar ≤ laatste_jaar`).

## T2. Peilmomenten (één inschrijving per persoon × 1 oktober over het bestuur)
- **Doel:** spec §4, `peilmomenten`.
- **Bestanden:** `src/staat_mbo/loopbaan.py`, `tests/test_loopbaan.py`.
- **Tests eerst** (bouw een mini-`fact_inschrijving_schooljaar` in de test):
  - Persoon op 1-10-2022 met n2 (BRIN A) en n3 (BRIN B) → 1 rij, `Niveau 3`, `BRIN B`.
  - Gelijk niveau: crebo 25191 en 25475 → het laagste crebo `25191`.
  - Gelijk niveau en crebo, `DatumBegin` 2021-08-01 en 2022-08-01 → de recentste.
  - Alleen een inschrijving zonder niveau → 1 rij met `Niveau` null (de persoon telt als aanwezig).
  - Niveau zonder niveau-info naast n2 → n2 gekozen.
  - Twee jaren → 2 rijen; `Jaar` = `Schooljaar`, type i32.
  - `Niveau` van "MBO-3" → 3 (i32).
  - Uniek per (`_persoon_id`, `Jaar`): `df.select(...).is_duplicated().any() is False`.
- **Stappen:** `peilmomenten(star)`; `niveau_getal` uit `naar_1cho._niveau_getal` kopiëren (naar_1cho verdwijnt in T19); `eerste_peiljaar` hierheen verhuizen en in `naar_1cho` importeren uit `loopbaan`.
- **Afhankelijk van:** T0.
- **Klaar:** tests groen; `test_naar_1cho` nog groen.

## T3. Diploma's met jaartijdvak en niveau van het diploma
- **Doel:** spec §4, `diplomas`.
- **Bestanden:** `src/staat_mbo/loopbaan.py`, `tests/test_loopbaan.py`.
- **Tests eerst** (een mini-`fact_inschrijving` + `dim_opleiding`):
  - Diploma 2024-09-30 → `Jaartijdvak 2023`; 2024-10-01 → `2024` (grensgeval).
  - Hetzelfde diploma op drie periode-rijen → 1 rij (uniek).
  - Diploma-crebo n2 op een inschrijving met `Opleidingcode` n3 → `Niveau 2` (van het diploma, niet van de inschrijving).
  - Diploma-crebo zonder niveau in `dim_opleiding` → niveau via `mbo_bekostiging_bestanden.opleidingsniveau.vul_niveau_aan`; bekend in referentiedata → ingevuld, onbekend → null.
  - `Leertraject` en `BRIN` komen van de inschrijvingsrij.
  - Rijen zonder `DIP_DatumResultaat` vallen weg.
- **Stappen:** `jaartijdvak(datum: pl.Expr)` (= de huidige `diplomajaar`, hernoemd; `naar_1cho` importeert hem tot T19) en `diplomas(star)`.
  - Een v4-guardtest: `from mbo_bekostiging_bestanden.opleidingsniveau import vul_niveau_aan` en `from mbo_bekostiging_bestanden.waardenlijsten import leertrajecten_buiten_indicatorpopulatie` importeren. Zo faalt een v4-upgrade die deze weghaalt meteen.
- **Afhankelijk van:** T0.
- **Klaar:** tests groen.

## T4. Nominale duur verhuizen naar `duur.py`
- **Doel:** zuivere verhuizing; het gedrag blijft gelijk.
- **Bestanden:** `src/staat_mbo/duur.py` (nieuw), `src/staat_mbo/naar_1cho.py` (importeert uit duur), `tests/test_duur.py` (verplaatst uit `test_naar_1cho.py`).
- **Tests eerst:** verplaats de bestaande `nominale_duur`/`opleidingen_met_standaardduur`-tests ongewijzigd en laat ze eerst falen op de import uit `staat_mbo.duur`. Extra test: `duur_per_opleiding(duur, opleidingen)` geeft `Duur` en `Duur_bron` ∈ {"geplande einddatum", "standaard"}:
  - een opleiding in `duur` → bron "geplande einddatum";
  - een n4-opleiding zonder eigen duur → `Duur=4`, bron "standaard".
- **Stappen:**
  1. Verplaats `MIN_INSCHRIJVINGEN_DUUR`, `STANDAARDDUUR`, `nominale_duur` en `opleidingen_met_standaardduur`.
  2. Voeg `duur_per_opleiding` toe.
- **Afhankelijk van:** T0.
- **Klaar:** alle tests groen, ook die van `naar_1cho`.

## T5. Jaarresultaat per jaartijdvak
- **Doel:** spec §5.1. `jaarresultaat(pm, dip, w) -> DataFrame[Jaartijdvak, Opleidingcode, Niveau, Leertraject, Teller, Noemer]`.
- **Bestanden:** `src/staat_mbo/indicatoren.py`, `tests/test_indicatoren_jr.py`.
- **Tests eerst** (`waarneming(2018, 2025)`, opleiding A = 25498 n2 BOL, B = 25475 n3 BOL):
  - s1: `P(2022)` A, diploma A 2023-06-30, niet in `P(2023)` → G.
  - s2: `P(2022)` A, niet in `P(2023)`, geen diploma → U.
  - s3: `P(2022)` A, `P(2023)` A, geen diploma → erbuiten.
  - s4: niet in `P(2022)`, diploma A 2023-07-01 (instroom na 1 oktober) → G.
  - s5: `P(2022)` A, diploma A 2023-09-15 → G in 2022.
  - s6: `P(2022)` A, niet in `P(2023)`, diploma A 2023-10-01 → U in 2022 (het diploma valt in jaartijdvak 2023).
  - s7: `P(2022)` A, diploma A 2023-06-30, `P(2023)` B (gestapeld) → G voor A.
  - **Verwacht A 2022: Teller 4 (s1, s4, s5, s7), Noemer 6 (+ s2, s6).**
  - s8: diploma's A 2022-12-01 en B 2023-07-01 → één keer, voor B in 2022 (Teller B = 1, en s8 telt niet bij A).
  - Entree (n1), diploma n1 → niet in de uitvoer.
  - `Leertraject` "OVO" → niet in de uitvoer.
  - Jaartijdvak 2025 (2026 niet waarneembaar) → geen rijen voor 2025.
  - Gat in 2023 → geen rijen voor 2022 en 2023.
- **Afhankelijk van:** T1, T2, T3.
- **Klaar:** tests groen.

## T6. Diplomaresultaat per jaartijdvak
- **Doel:** spec §5.2. `diplomaresultaat(...) -> [..., Teller, Noemer, Volledig]`.
- **Bestanden:** `src/staat_mbo/indicatoren.py`, `tests/test_indicatoren_dr.py`.
- **Tests eerst** (opleiding B n3, jaartijdvak 2022):
  - d1: `P(2022)` B, niet in `P(2023)`, diploma A (n2) 2019-06-30 → teller (stapelaar die uitvalt).
  - d2: idem, maar diploma 2017-06-30 (vóór 1-10-2017) → alleen noemer.
  - d3: weg zonder diploma → noemer.
  - d4: `P(2023)` B → erbuiten.
  - d5: weg, diploma B 2023-08-15 → teller.
  - d6: entree-verlater → niet in de uitvoer.
  - d7: op 1-10-2023 alleen een OVO-inschrijving bij een andere eigen BRIN → geen verlater.
  - **Verwacht B 2022: Teller 2, Noemer 4.**
  - `Volledig`: met `waarneming(2018, 2025)` (`diplomas_vanaf` 2018-08-01) is 2022 `False` (1-10-2017 < 2018-08-01). Met `waarneming(2014, 2025)` is het `True`.
  - Grens: diploma op 2017-10-01 telt mee voor t = 2022; op 2017-09-30 niet.
- **Afhankelijk van:** T1, T2, T3.
- **Klaar:** tests groen.

## T7. Startersresultaat per jaartijdvak
- **Doel:** spec §5.3. `startersresultaat(...) -> [..., Teller, Noemer, Terugblik]`.
- **Bestanden:** `src/staat_mbo/indicatoren.py`, `tests/test_indicatoren_sr.py`.
- **Tests eerst** (`waarneming(2014, 2025)`, A n2, t = 2022):
  - n1: nieuw, `P(2023)` A → teller.
  - n2: nieuw, weg, diploma A 2023-07-01 → teller.
  - n3: nieuw, weg zonder diploma → noemer.
  - n4: ook in `P(2017)` → niet nieuw.
  - n5: ook in `P(2015)` (7 jaar terug) → nieuw.
  - n6: nieuw, `P(2023)` entree (n1) → noemer.
  - n7: nieuw, `P(2023)` B (n3) zonder diploma → teller (opgestroomd).
  - **Verwacht A 2022: Teller 3, Noemer 6, Terugblik 6.**
  - Verkorte terugblik: `waarneming(2020, 2025)` geeft voor t = 2022 `Terugblik 2`, en n4 (in `P(2017)`) telt dan als nieuw.
  - t = `eerste_jaar` (k = 0) → geen rijen.
  - Een starter in entree → niet in de uitvoer.
- **Afhankelijk van:** T1, T2, T3.
- **Klaar:** tests groen.

## T8. Driejaarscijfer, groepering en norm
- **Doel:** spec §5.4. `driejaarscijfer(eenjaars, indicator, w, groep) -> DataFrame`, met `groep` ∈ {"instelling", "niveau", "opleiding", "opleiding_leerweg"}.
- **Bestanden:** `src/staat_mbo/indicatoren.py`, `tests/test_driejaarscijfer.py`.
- **Tests eerst:**
  - Het voorbeeld uit de regeling: A n2, 2020 5/20, 2021 30/40, 2022 40/40 → periode t/m 2022: Teller 75, Noemer 100, `Percentage 75.0`, `Norm 67` (JR n2), `Onder_norm False`.
  - DR n3, 69,9% → `Norm 70`, `Onder_norm True`. SR n2 → `Norm 79`.
  - 2019 niet waarneembaar → geen periode t/m 2021.
  - Opleiding zonder rij in 2021 maar met 2020 en 2022 → het jaar telt als 0/0, en de periode bestaat.
  - Noemer 11 → `Te_klein True`; noemer 12 → `False`.
  - `groep="instelling"` → `Norm` null; `groep="niveau"` telt de crebo's per niveau op.
  - `Volledig` = alle drie de jaren volledig (DR: `Volledig`; SR: `Terugblik == 6`; JR: altijd `True`).
  - `Periode`-label: "2020-2021 t/m 2022-2023".
  - De normen komen uit `mbo_bekostiging_bestanden.indicatoren.norm_voor` ("jr"/"dr"/"sr", niveau, "voldoende"). Guardtest: `norm_voor("sr", 2, "voldoende") == 79`, `norm_voor("dr", 3, "voldoende") == 70`, `norm_voor("jr", 4, "voldoende") == 68` (gelijk aan regeling art. 5–7).
- **Afhankelijk van:** T1 (Waarneming); het schema uit T5–T7 (alleen de kolomnamen; kan parallel).
- **Klaar:** tests groen.

## T9. Instroomcohorten met herkomst
- **Doel:** spec §5.5, cohort en herkomst. `instroomcohorten(pm, dip, w) -> [_persoon_id, Cohort, Opleidingcode, Niveau, Leertraject, Herkomst, Terugblik]`.
- **Bestanden:** `src/staat_mbo/cohorten.py`, `tests/test_cohorten.py`.
- **Tests eerst** (`waarneming(2016, 2025)`):
  - Eerste keer in `P(2020)` A, `DatumBegin` 2020-08-15 → cohort 2020, `Herkomst "nieuw"`.
  - In `P(2020)` A met `DatumBegin` 2019-08-01 en `eerste_jaar` 2020 (`waarneming(2020, 2025)`) → niet in de cohorten (links afgekapt).
  - Diploma A (n2) 2021-06-30, `P(2021)` B (n3) → cohort B 2021, `Herkomst "na diploma"`.
  - `P(2020)` A (n2), `P(2021)` B (n3) zonder diploma → cohort B 2021, `Herkomst "ander niveau zonder diploma"`.
  - `P(2020)` 25498 (n2), `P(2021)` 25225 (n2) → `Herkomst "wissel"`.
  - Een crebo-opvolger (dim_opleiding `Opleiding_opvolger`: 25498 → 25999) geldt als dezelfde opleiding → geen nieuwe cohortrij.
  - Eerst checken hoe vaak `Opleiding_opvolger` in `demo_star` en in de v4-referentiedata gevuld is. Is dat leeg, noteer het in de PR en zet de test op `xfail` met de reden.
  - Rijen met `Niveau` null of `Leertraject` OVO/ODT doen niet mee.
- **Afhankelijk van:** T1, T2, T3.
- **Klaar:** tests groen.

## T10. Rendement nominaal en nominaal + 1
- **Doel:** spec §5.5. `rendement(cohorten, dip, duur, w) -> per cohortrij: Duur, Duur_bron, Nominaal (bool/null), Nominaal_plus_1, In_eigen_opleiding`, plus `rendement_per_groep(...)` met aantallen en percentages, waarbij null niet meetelt.
- **Bestanden:** `src/staat_mbo/cohorten.py`, `tests/test_rendement.py`.
- **Tests eerst** (cohort 2020, A n2, duur 2, `waarneming(2016, 2025)`):
  - Diploma A 2022-06-30 → `Nominaal True`, `In_eigen_opleiding True`.
  - Diploma 2022-09-30 → `True`.
  - Diploma 2022-10-01 → `Nominaal False`, `Nominaal_plus_1 True`.
  - Diploma n3 (ander crebo) 2022-06-30 → `True`, `In_eigen_opleiding False`.
  - Cohort n3 met alleen een n2-diploma (afgestroomd) → `Nominaal False`.
  - `waarneming(2016, 2021)`: cohort 2020 duur 2 → `Nominaal null` (nog niet waarneembaar). Duur 1 → waarneembaar.
  - Gat in 2021 → null.
  - `rendement_per_groep`: 3 cohortrijen, 1 `True`, 1 `False`, 1 null → `Percentage 50.0`, `Nog_niet_waarneembaar 1`.
- **Afhankelijk van:** T4, T9.
- **Klaar:** tests groen.

## T11. Uitval en loopbaanstatus
- **Doel:** spec §5.5. `uitval(cohorten, pm, dip, w, x)` en `loopbaanstatus(cohorten, pm, dip, w, k)` (9 categorieën, als constante `CATEGORIEEN` in vaste volgorde).
- **Bestanden:** `src/staat_mbo/cohorten.py`, `tests/test_loopbaanstatus.py`.
- **Tests eerst** (cohort 2020, A n2, k = 1, één student per categorie):
  1. Diploma A 2021-06-30, `P(2021)` n3 → "Diploma, verder op hoger niveau".
  2. Diploma, niet in `P(2021)` → "Diploma, vertrokken".
  3. Diploma, `P(2021)` n2 ander crebo → "Diploma, nog ingeschreven op hetzelfde of lager niveau".
  4. `P(2021)` A, geen diploma → "Zonder diploma, zelfde opleiding".
  5. `P(2021)` ander n2-crebo → "Zonder diploma, ander crebo op hetzelfde niveau".
  6. `P(2021)` n3 → "Zonder diploma, hoger niveau".
  7. `P(2021)` n1 → "Zonder diploma, lager niveau".
  8. Niet in `P(2021)` → "Vertrokken zonder diploma".
  9. `waarneming(2016, 2020)` → "Nog niet waarneembaar".
  - Uitval: categorie 8 → `uitval(x=1) True`.
  - Vertrokken in 2021, terug in 2022 → `uitval(x=2) False`.
  - Entree-diploma telt als diploma bij uitval.
  - De som van de categorieën = het aantal cohortrijen (geen dubbelingen).
- **Afhankelijk van:** T9.
- **Klaar:** tests groen.

## T12. Meldingen bij te weinig historie
- **Doel:** spec §7. `meldingen(w, analyse_feiten) -> list[Melding(ernst, tekst)]`.
- **Bestanden:** `src/staat_mbo/historie.py`, `tests/test_historie.py`.
- **Tests eerst:**
  - `waarneming(2020, 2025)` (de huidige demodata, 6 × 1 oktober):
    - geen JR-melding (er is een driejaarscijfer);
    - een DR-melding met "diploma's van vóór 01-08-2020" en de jaren 2022–2024;
    - een SR-melding met "4 jaar terug in plaats van 6" (de grootste terugblik voor t = 2024);
    - de rendementsmelding voor niveau 4.
  - `waarneming(2022, 2024)` (3 × 1 oktober) → JR "minstens 4 nodig", SR "nog geen driejaarscijfer".
  - `waarneming(2016, 2025)` → geen DR- en SR-meldingen.
  - Gat in 2022 → de melding noemt het gat en de jaren zonder cijfer.
  - Tekst-snapshot: één test die de exacte zinnen vastlegt (spec §7).
- **Stappen:** `stapelcontrole._MIN_JAREN` en de bijbehorende melding weghalen (met de test daarvan).
- **Afhankelijk van:** T1.
- **Klaar:** tests groen.

## T13. Analyse-object, `samenvoegen` en `smbo staat` zonder R
- **Doel:** spec §4/§9. `analyse.maak_analyse(invoer, werkmap) -> Analyse` (de dataclass met star-afgeleiden, `Waarneming`, `duur`, `Stapelrapport`, `meldingen`), en daarop de CLI.
- **Bestanden:** `src/staat_mbo/analyse.py`, `src/staat_mbo/samenvoegen.py`, `src/staat_mbo/cli.py`, `tests/test_analyse.py`, `tests/test_samenvoegen.py`, `tests/test_cli.py`.
- **Tests eerst:**
  - `maak_analyse(sorted(RUW.iterdir()), tmp)` op de fixtures → `analyse.rapport.ok`, `peilmomenten` niet leeg, `waarneming.eerste_jaar ≤ laatste_jaar`.
  - Een kapot bestand → `rapport.ok is False` met de fouttekst uit `InvoerFout` (gedrag zoals de huidige samenvoegen-test).
  - `smbo samenvoegen <fixtures> --uitvoer tmp` → exitcode 0; `meldingen.txt`, `stapelcontrole.json`, `peilmomenten.parquet` en `diplomas.parquet` bestaan; **geen** `1cho_mbo.csv`.
  - `smbo staat <fixtures> --uitvoer tmp` → `studiesucces.csv` (kolommen `Indicator, Periode, Groep, Opleidingcode, Niveau, Leertraject, Teller, Noemer, Percentage, Norm, Onder_norm, Te_klein, Volledig`), `cohorten.csv`, `loopbanen.csv`, `meldingen.txt`; exitcode 0. Een kapotte invoer → exitcode 1.
  - `smbo staat` roept geen `Rscript` aan (monkeypatch `shutil.which` → None, en het werkt toch).
- **Afhankelijk van:** T2–T12.
- **Klaar:** tests groen; `test_r.py` mag nog bestaan, maar `staat` gebruikt R niet meer.

## T14. Streamlit-app: skelet en startpagina
- **Doel:** spec §8.1. De app in het pakket, zodat `uv tool install` werkt.
- **Bestanden:** `src/staat_mbo/app/__init__.py`, `main.py`, `start.py`, `invoer.py`, `ui.py`; `tests/test_app_start.py`; demodata in het pakket. Eerst kijken: `demodata/` is 436K. Maak via `[tool.hatch.build.targets.wheel.force-include]` `demodata` beschikbaar als `staat_mbo/demodata`, of verplaats het naar `src/staat_mbo/demodata` en pas `scripts/maak_demodata.py` (`DOEL`) aan. Kies het verplaatsen en laat in de README een link staan.
- **Tests eerst** (`streamlit.testing.v1.AppTest`):
  - `invoer.synchroniseer_selectie([("a/../RO_x.csv", b"1")], werkmap)` → het bestand staat als `werkmap/selectie/RO_x.csv` (geen padontsnapping); een oud bestand dat niet meer gekozen is, wordt verwijderd. Dit is het gedrag van v4 `_invoer`.
  - AppTest op `start.py`: klik "Probeer met demodata" → `session_state["analyse"]` gezet, er verschijnt een succesmelding met "Gelukt", en er staan meldingen uit `historie`.
  - AppTest: Samenvoegen zonder bestanden → `st.warning` "Kies eerst je bestanden".
  - Een geïnjecteerde analyse met `rapport.ok False` → `st.error` met de fouttekst, en de pagina's blijven verborgen of tonen "Voeg eerst je bestanden samen".
  - `env STAAT_MBO_INVOER=<map>` → de app laadt die invoer bij de start. Dat gebruiken de opname en de tests.
- **Stappen:**
  1. `main.py` met `st.set_page_config(layout="wide")` en `st.navigation`, met de pagina's Start, Studiesucces, Cohorten, Loopbanen en Over de cijfers (in de pagina's van T15–T18 eerst een placeholder).
  2. `ui.py` met de gedeelde helpers: de filters in de zijbalk, `toon_tabel(df, naam)` met een download-knop, de vaste melding "Indicatief…" en een gecachete berekening (`st.cache_data` op een hash van de invoer).
  - Stijl als de v4-app: Altair, `hide_index`, en `help=`-teksten.
- **Afhankelijk van:** T13.
- **Klaar:** tests groen; `uv run streamlit run src/staat_mbo/app/main.py` toont de startpagina met de demodata (handmatig nagaan en een screenshot in de PR).

## T15. Pagina Studiesucces
- **Doel:** spec §8.2.
- **Bestanden:** `src/staat_mbo/app/studiesucces.py`, `tests/test_app_studiesucces.py`.
- **Tests eerst** (AppTest met een analyse uit de fixtures of een kleine synthetische analyse):
  - Er zijn drie metric-tegels met de labels "Jaarresultaat", "Diplomaresultaat" en "Startersresultaat".
  - De tabel heeft de kolommen Opleiding, Niveau, Leerweg, JR, DR, SR, n en Norm.
  - Een rij met `Te_klein` toont "te weinig studenten" en geen getal.
  - De pagina bevat de tekst "Indicatief" en **niet** de woorden "oordeel" of "voldoende studiesucces" (guard tegen een oordeel; behalve in de zin "Geen inspectieoordeel").
  - Met filter niveau = 3 bevat de tabel alleen niveau 3.
  - Een onvolledig DR-cijfer toont het icoon of de tekst "onvolledig".
- **Afhankelijk van:** T14.
- **Klaar:** tests groen; een screenshot met de demodata in de PR.

## T16. Pagina Cohorten
- **Doel:** spec §8.3.
- **Bestanden:** `src/staat_mbo/app/cohorten.py`, `tests/test_app_cohorten.py`.
- **Tests eerst:**
  - Er is een instroomgrafiek met de herkomstcategorieën.
  - De rendementstabel heeft de kolommen Cohort, Opleiding, Duur, "Duur uit", "Nominaal %", "Nominaal + 1 %" en "Nog niet waarneembaar".
  - Een recent cohort toont "nog niet waarneembaar" in plaats van 0%.
  - Uitval na 1 jaar is aanwezig.
- **Afhankelijk van:** T14 (rekent met T10 en T11).
- **Klaar:** tests groen.

## T17. Pagina Loopbanen (stapelen)
- **Doel:** spec §8.4.
- **Bestanden:** `src/staat_mbo/app/loopbanen.py`, `tests/test_app_loopbanen.py`.
- **Tests eerst:**
  - Met de keuze "na 1 / 2 / 3 jaar" telt het totaal per cohort op tot 100% (de tabel onder de grafiek).
  - De niveau-overgangsmatrix heeft n1..n4 en "weg" als kolommen.
  - De volgorde en de kleuren van de categorieën zijn vast (`CATEGORIEEN` uit T11).
  - Bij "studiewissel" staat de uitleg "stapelen telt niet als wissel".
- **Afhankelijk van:** T14.
- **Klaar:** tests groen.

## T18. Pagina Over de cijfers
- **Doel:** spec §8.5.
- **Bestanden:** `src/staat_mbo/app/over.py`, `src/staat_mbo/definities.py` (teksten op één plek, ook gebruikt als `help=` in T15–T17), `tests/test_app_over.py`.
- **Tests eerst:**
  - Elke indicator uit §5 heeft een definitie in `DEFINITIES`.
  - De pagina bevat de links naar stcrt-2022-18467 en stb-2022-273.
  - Er is een dekkingstabel indicator × jaartijdvak met de waarden "ja", "onvolledig" en "nee".
- **Afhankelijk van:** T14.
- **Klaar:** tests groen.

## T19. `smbo dashboard` op Streamlit; R en 1CHO eruit
- **Doel:** spec §9. De R-brug en de 1CHO-vertaling verwijderen.
- **Bestanden:**
  - Aanpassen: `src/staat_mbo/cli.py` en `src/staat_mbo/stapelcontrole.py` (teksten zonder staat1cho; aliassen weg).
  - Verwijderen: `r.py`, `r/`, `naar_1cho.py`, `tests/test_r.py`, het restant van `tests/test_naar_1cho.py`.
  - Aanpassen: `tests/test_cli.py`.
  - Bovenaan de oude spec en het oude plan in `docs/superpowers/` een verwijzing naar het nieuwe ontwerp.
- **Eerst:** open vraag 5 moet beantwoord zijn (alles weg, of een 1CHO-export één versie houden).
- **Tests eerst:**
  - `smbo dashboard --poort 8599 --geen-browser` roept `subprocess.run([sys.executable, "-m", "streamlit", "run", <pad naar app/main.py>, "--server.port", "8599", "--server.headless", "true"], ...)` aan (monkeypatch).
  - `--invoer X` zet `STAAT_MBO_INVOER`.
  - `smbo --help` noemt geen R.
  - `grep -r "Rscript\|staat1cho" src/` is leeg (als test op de broncode).
  - De stapelcontrole-melding bij ongelijk einde zegt "we rekenen tot {jaar}".
- **Afhankelijk van:** T15–T18.
- **Klaar:** de hele suite groen; `smbo dashboard` start handmatig de app.

## T20. Toets op echte data (Aslam, buiten de agent)
- **Doel:** issue punt 5.
- **Werkwijze:** Aslam draait `smbo staat` op de RO's van één instelling.
- **Vergelijken:** het driejaarscijfer van JR, DR en SR per niveau naast de cijfers die de instelling van de Inspectie/DUO heeft. Verwacht: een verschil van enkele procentpunten (RO vs ROD).
- **Uitkomsten noteren:** de verschillen > 5 pp, de looptijd en de meldingen.
- **De agent levert alleen** een checklist in de PR-beschrijving. Hij krijgt de data niet te zien en zet geen uitkomsten op studentniveau in git.
- **Afhankelijk van:** T19.
- **Klaar:** Aslam heeft de bevindingen genoteerd; de definitie aangepast als dat nodig is (dan een nieuwe taak).

## T21. Demodata met stapelen, opstromen en afstromen
- **Doel:** issue punt 4: de demo laat het mbo-verhaal zien.
- **Bestanden:** `scripts/maak_demodata.py`, `src/staat_mbo/demodata/*` (of `demodata/`, zie T14), `tests/test_demodata.py`.
- **Eerst:** open vraag 7 (6 of 10 jaar). Standaard in dit plan: **10 jaar, 5 RO's van twee jaar**, zodat SR en DR volledig te zien zijn. Het aantal studenten blijft onder de 2000 (`e3e5a74`).
- **Tests eerst** (op de gegenereerde bestanden via `maak_analyse`; met een vast zaadgetal zijn de uitkomsten deterministisch):
  - Er zijn ≥ 20 studenten die stapelen n1 → n2 (entree-diploma, daarna een n2-cohort met `Herkomst "na diploma"`).
  - Er zijn ≥ 30 die stapelen n2 → n3 en ≥ 15 die stapelen n3 → n4 (loopbaanstatus 1 na k = duur).
  - ≥ 15 stromen op zonder diploma (status 6).
  - ≥ 15 stromen af n3 → n2 of n2 → n1 (status 7).
  - ≥ 10 stapelaars vallen uit na een eerder diploma; daardoor ligt de DR van n3 boven die zonder die regel. Test: het DR-teller-aandeel van die groep is > 0.
  - Alle drie de Inspectie-indicatoren hebben voor elk niveau 2–4 ≥ 1 driejaarscijfer met `Volledig True`.
  - Per niveau ligt minstens één opleiding onder de norm en minstens één erboven (de demo laat beide zien).
  - `maak_demodata.py` twee keer draaien geeft bytes-identieke bestanden.
- **Stappen:**
  1. Stapelpaden toevoegen in `_volg_opleiding` (vervolgopleiding na een diploma met een kans per niveau).
  2. Op- en afstroom als een nieuwe inschrijving met reden `REDEN_WISSEL` op een ander niveau.
  3. Diploma's in augustus en september (een grensgeval voor het jaartijdvak).
  4. `LAATSTE_JAAR`/`EERSTE_JAAR` op 10 jaar zetten.
- **Afhankelijk van:** T19 (en T20 mag eerst).
- **Klaar:** tests groen; de app op de demodata toont alle categorieën.

## T22. README zonder R
- **Doel:** issue punt 6: een kortere installatie.
- **Bestanden:** `README.md` (CRLF behouden).
- **Tests eerst:** `tests/test_readme.py`:
  - de README noemt geen "R", "Rscript", "staat1cho" of "install.packages";
  - de installatie heeft precies twee stappen (uv en `uv tool install …`);
  - de commando's `smbo dashboard` en `smbo staat` staan erin;
  - de link naar `docs/superpowers/specs/<nieuw ontwerp>.md` bestaat.
- **Stappen:**
  1. Herschrijven: wat je nodig hebt, installeren (2 stappen), gebruiken (upload → Samenvoegen → pagina's), zonder scherm, goed om te weten (indicatief, RO vs ROD, één bestuur, historie per indicator, persoonsgegevens) en meer weten (met de bronnen §3).
  2. `spec.md` als `docs/superpowers/specs/2026-11-xx-staat-mbo-dashboard-design.md` en dit plan als `docs/superpowers/plans/…` in de repo zetten.
- **Afhankelijk van:** T21.
- **Klaar:** test groen, en Aslam heeft de tekst gelezen.

## T23. Demovideo opnieuw
- **Doel:** issue punt 6.
- **Bestanden:** `demo-video/stappen.py`, `demo-video/scenes/record.py`, `demo-video/stitch.py`, `demo-video/README.md`.
- **Gebruik:** de skill `demo-video`. Start de app met `STAAT_MBO_INVOER=<demodata>` op een vaste poort (`smbo dashboard --poort 8599 --geen-browser`).
- **Tests eerst:** de bestaande regel "een kader mag niets raken" blijft (de opname faalt bij overlap). Voeg een test toe op `stappen.py`: elke stap heeft een ondertitel van ≤ 110 tekens en een uitspraak, en de stap-id's zijn uniek.
- **Stappen:** de scènes zijn start, demodata, Gelukt + meldingen, Studiesucces (tegels, tabel, normlijn, "indicatief"), Cohorten (rendement nominaal), Loopbanen (stapelen n2 → n3) en Over de cijfers.
  - De voice-over legt uit: "Stapelen telt niet als uitval of wissel."
  - Daarna de video via github.com in de README slepen (bestaande werkwijze, niet in git).
- **Afhankelijk van:** T22.
- **Klaar:** de video staat in de README en de opname draait zonder overlap.

## T24. Wiki bijwerken
- **Doel:** CLAUDE.md, CEDANL-wiki.
- **Werkwijze:** de skill `wiki-update`.
  - `wiki/projects/staat-van-onderwijsinstelling-mbo.md`: de status, **Bestanden** (de nieuwe modules en `app/`) en de beslissingen (geen 1CHO, geen R, een eigen regeling-logica).
  - `wiki/concepts/`: een nieuwe pagina `studiesucces-mbo.md` met JR, DR en SR, het jaartijdvak, het driejaarscijfer, de normen en de bronnen, plus de `*zoek:*`-termen in `index.md`.
  - `mbo-bekostiging-bestanden.md`: de opmerking dat de JR/DR-proxy afwijkt van de regeling.
- **Afhankelijk van:** T23 (of na elke gemergde reeks).
- **Klaar:** gecommit en gepusht in `cedanl-wiki-aslam`.
