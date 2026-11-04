# Ontwerp: Staat van de Onderwijsinstelling MBO als eigen dashboard (zonder R)

Issue: cedanl/staat-van-onderwijsinstelling-mbo#6 · Datum: 2026-11-04 · Status: ontwerp, nog niet gebouwd
Basis: pitch-branch `c7645e6` (9 commits vóór `main`), `mbo-bekostiging-bestanden` v4.0.0 (`05d5c5b`).

---

## 1. Samenvatting

- Eén Streamlit-app in deze repo (`smbo dashboard`): uploaden, samenvoegen en dashboard. Geen R.
- **Invoer blijft de star van v4.** We lezen `fact_inschrijving_schooljaar`, `fact_inschrijving`, `dim_opleiding` en `meta_leveringen` rechtstreeks.
- **De 1CHO-vorm gaat eruit.** Daarvoor in de plaats komt een kleine mbo-tussenlaag in deze repo: `peilmomenten` (persoon × 1 oktober), `diplomas` (persoon × diploma) en `Waarneming` (welke 1 oktobers we zien).
- **De JR/DR-vlaggen van v4 gebruiken we niet.** Ze wijken op wezenlijke punten af van de Regeling studiesucces mbo (§3), en v4 heeft besloten dat ze proxy blijven (#296). Wel hergebruiken we uit v4: de pipeline, `indicatoren.norm_voor` (normen.toml = de voldoende-normen uit de regeling), de indicatorpopulatie per leertraject en de niveau-aanvulling.
- Indicatoren per opleiding (crebo) × niveau × leerweg:
  - **Inspectie-indicatoren:** jaarresultaat, diplomaresultaat en startersresultaat, als driejaarscijfer, met de norm per niveau. Overal staat "indicatief" bij. Er komt geen oordeel.
  - **Cohorten:** instroom, rendement nominaal en nominaal + 1, en uitval.
  - **Loopbanen:** stapelen, opstromen, afstromen en studiewissel als aparte uitkomsten.

## 2. Architectuurkeuze: v4-star als invoer, eigen mbo-tussenlaag, geen 1CHO

### Opties

| Optie | Wat | Oordeel |
|---|---|---|
| A. 1CHO-vorm als tussenlaag houden | `naar_1cho` blijft, Python-indicatoren rekenen op 1CHO-kolommen | Nee |
| B. v4-star rechtstreeks, inclusief de JR/DR-vlaggen | `indicatoren.rendement()` van v4 aanroepen; alleen SR erbij bouwen | Nee |
| **C. v4-star als invoer, eigen mbo-tussenlaag, eigen indicatorlogica** | Ster → `peilmomenten`/`diplomas`/`Waarneming` → indicatoren volgens de regeling | **Ja** |

### Waarom niet A (1CHO houden)
1. 1CHO bestond om `staat1cho` te voeden. Zonder R heeft het geen afnemer meer. Uit de spike (#4): 47 van de 115 kolommen zijn te vullen, en de hbo/wo-kaarten blijven leeg.
2. De vorm gooit weg wat het mbo nodig heeft:
   - de exacte diplomadatum (de regeling rekent met een jaartijdvak van 1-10 t/m 30-9, 1CHO met een diplomajaar);
   - het niveau van een diploma los van de inschrijving (DR telt ook een eerder diploma op een lager niveau);
   - de aanwezigheid op elke 1 oktober over het hele bestuur (instellingsverlater);
   - de waarneembaarheid per BRIN.
3. `naar_1cho._diplomas` kent kunstgrepen: een diploma "valt op de laatste rij van de student". Juist die leiden tot de misleiding uit de issue (stapelaar telt als "Diploma behaald").
4. Wat bruikbaar is, verhuist: de keuze van de hoofdinschrijving over het bestuur, `nominale_duur`, `eerste_peiljaar` en `diplomajaar` (= jaartijdvak).

### Waarom niet B (JR/DR-vlaggen van v4 rechtstreeks)
De issue zegt: "Jaar- en diplomaresultaat zitten al in de star". Dat klopt maar half. Zo wijkt v4 af van de regeling (`src/mbo_bekostiging_bestanden/schooljaar.py`, `quality.INDICATOREN_STATUS`):

| Punt | Regeling studiesucces mbo | v4 (`_jr_*`, `_dr_*`) |
|---|---|---|
| JR-noemer | gediplomeerden + ongediplomeerde instellingsverlaters; wie zonder diploma blijft, telt niet mee | **alle** hoofdinschrijvingen op 1-10-t (v4 noemt dit zelf `noemer_inclusief_ongediplomeerden`) |
| Periode | jaartijdvak 1-10-t t/m 30-9-(t+1) | schooljaar 1-8-t t/m 31-7-(t+1); een diploma in aug/sep valt in het verkeerde jaar |
| JR-teller | elk diploma niveau 2–4 in het jaartijdvak, ook van wie pas na 1 oktober instroomde | alleen hoofdinschrijvingen op 1 oktober |
| Eén keer per instelling | per instelling één inschrijving | hoofdinschrijving per **BRIN** (een student met twee BRIN's van één bestuur telt twee keer) |
| DR-diplomavenster | jaartijdvak plus de 5 jaar ervoor (vanaf 1-10-(t-5)) | vanaf 1-8-(t-5) tot 1-10-(t+1); bijna gelijk |
| Instellingsverlater | op 1-10-t ingeschreven, op 1-10-(t+1) niet bij de instelling | niet ingeschreven bij welke instelling in de dataset ook; gelijk als de dataset = de instelling |
| SR | wél | ontbreekt |
| Driejaarscijfer | tellers en noemers over 3 jaartijdvakken opgeteld | ontbreekt (v4: "geen formeel 3-jaarsvenster") |

Als we de vlaggen hergebruiken, erven we de grootste afwijking (de JR-noemer). Die maakt de JR systematisch lager dan die van de Inspectie. Een startersresultaat ernaast bouwen kan alleen als we de logica toch voor een deel zelf schrijven.

### Waarom C
- **Aansluiting op v4 blijft maximaal.** Invoer, pseudonimisering, stapelen, canonicalisatie, de schooljaar-grain, het niveau (CREBO/S-BB) en de normen komen uit v4. We rekenen alleen het laatste stukje zelf.
- De tussenlaag is klein (twee tabellen en een object) en mbo-eigen. Op één plek staan dan de regels voor "één inschrijving per instelling per 1 oktober" en "welk diploma, met welk niveau en welk jaartijdvak".
- Alle drie de indicatoren, de cohorten en de loopbanen rekenen op dezelfde twee tabellen. Ze tellen dus hetzelfde.
- Later kan de indicatorlogica naar v4 als publieke module (`indicatoren`, #294), als v4 dat wil. Dat is een open vraag (§12), geen voorwaarde.

### Risico van C
- Er bestaan dan twee JR/DR-getallen binnen CEDA: de v4-proxy en de regeling-variant hier. Oplossing: beide zeggen expliciet wat ze zijn, en onder "Over de cijfers" staat waarom ze verschillen. We melden de JR-noemer upstream (open vraag 1).
- We gebruiken een paar interne v4-functies (`opleidingsniveau.vul_niveau_aan`, `waardenlijsten.leertrajecten_buiten_indicatorpopulatie`). Die zijn importeerbaar, maar geen beloofde API. Dat werkt zolang de pin op `05d5c5b` blijft. Een test vangt het op als een v4-upgrade iets breekt.

## 3. Bronnen en definities

### Geldende regels (nagetrokken 2026-11-04)
- **Regeling studiesucces mbo** (Regeling van 24 juni 2022, nr. MBO/30739616), Stcrt. 2022, 18467, in werking sinds 1-8-2022. Op wetten.overheid.nl (BWBR0046913) staat ze als geldend sinds 1-8-2022 t/m heden, zonder latere wijziging. Dit is **de vastgestelde versie, niet meer de consultatieversie** die de issue noemt.
  - https://zoek.officielebekendmakingen.nl/stcrt-2022-18467.pdf
  - https://wetten.overheid.nl/BWBR0046913/2022-08-01/0
  - Consultatieversie (ter vergelijking): https://internetconsultatie.nl/succesmbo/document/8837
- **Uitvoeringsbesluit WEB, hoofdstuk 4A** (art. 4a.1 begrippen, art. 4a.2 maatstaven), Stb. 2022, 273: https://zoek.officielebekendmakingen.nl/stb-2022-273.pdf
- **DUO, Toelichting berekende indicatoren GJ mbo 2024** (de categorieën doorstromer/uitstromer met/zonder diploma): https://duo.nl/open_onderwijsdata/images/2024-toelichting-berekende-indicatoren.pdf
- **Onderzoekskader mbo:** volgens de regeling blijft de werkwijze van het onderzoekskader 2021 gelijk. Er is een versie per 1-8-2024 (https://eerstekamer.nl/9370000/1/j4nvi0xeni9vr2l_j9vvkfvj6b325az/vmel8tnqjfb5/f=/vmel8ux06hh0.pdf; staat van wijzigingen: https://onderwijsinspectie.nl/binaries/onderwijsinspectie/documenten/publicaties/2024/06/12/staat-van-wijzigingen-onderzoekskaders-2024/Staat+van+Wijzigingen+Onderzoekskaders+2024.pdf). **Onzeker:** de tekst over studiesucces in het kader van 2024 heb ik niet kunnen lezen. De staat van wijzigingen leverde geen leesbare tekst op. De regeling gaat voor op het kader.
- **Onzeker:** v4 noemt als bron "Definitie indicatoren en toelichting bestanden onderwijsresultaten voor het bekostigd MBO" (31 mei 2024). Daaruit komen de minimale noemer van 12, de hoge normen en de uitsluiting van OVO/ODT. Online heb ik dat document niet gevonden. De voldoende-normen in `normen.toml` zijn wel gelijk aan de regeling.

### Begrippen (UWEB art. 4a.1, regeling art. 1–4)
- **Jaartijdvak t:** 1-10-t t/m 30-9-(t+1). We noemen het met het jaar van de begindatum ("2023" = 1-10-2023 t/m 30-9-2024) en tonen het als "2023-2024".
- **Peildatum:** 1 oktober.
- **Gediplomeerde:** student of extraneus met een diploma van een beroepsopleiding op niveau 2, 3 of 4 bij de instelling.
- **Instellingsverlater (in jaartijdvak t):** op 1-10-t ingeschreven voor een beroepsopleiding bij de instelling, en op 1-10-(t+1) niet.
- **Een keer per instelling:** per student telt één inschrijving per instelling (per jaartijdvak). Welke inschrijving DUO/de Inspectie kiest, staat niet in de regeling. **Onzeker** (mbo-encyclopedie). Wij kiezen het hoogste niveau, dan het laagste crebo, dan het recentste begin. Dat is gelijk aan v4 en aan de huidige `_markeer_hoofdinschrijving`.
- **Entree** valt buiten alle drie de indicatoren (UWEB art. 4a.2, lid 2).
- **Extranei** tellen mee (toelichting art. 4). Leertraject `EX` hoort dus bij de populatie.
- **Driejaarscijfer:** tel de tellers en noemers van de laatste drie jaartijdvakken op en deel die (art. 4, lid 2). Voorbeeld uit de toelichting: (5+30+40)/(20+40+40) = 75%.
- **Normen voldoende** (art. 5–7), driejaarscijfer:

| Niveau | JR | DR | SR |
|---|---|---|---|
| 2 | 67% | 61% | 79% |
| 3 | 68% | 70% | 82% |
| 4 | 68% | 70% | 82% |

  Dit is gelijk aan `metadata/normen.toml` in v4, dus we lezen de normen via `mbo_bekostiging_bestanden.indicatoren.norm_voor`. De hoge normen in v4 gebruiken we niet: ze staan niet in de regeling en "hoog" zou een oordeel suggereren.
- **Beoordeling** (art. 8–9: 2 van de 3, maatwerk): **niet nabouwen** (de issue zegt: geen inspectieoordeel suggereren).

### Onze afbakening van "instelling" en "opleiding"
- **Instelling** = alle geüploade BRIN's samen (bestaand besluit: "tellen als één bestuur"). Een overstap tussen eigen BRIN's maakt iemand dus geen instellingsverlater. Onzeker voor een bestuur met meerdere instellingen: zie open vraag 2.
- **Opleiding** = crebo. We tonen de indicatoren op vier niveaus: instelling, niveau, crebo, crebo × leerweg. De norm hangt aan het niveau van het crebo.
- **Leerweg** = `Leertraject` van de gekozen inschrijving: BOL, BBL, BOL_DT, EX. OVO en ODT vallen buiten de indicatorpopulatie, net als in v4 (`leertrajecten_buiten_indicatorpopulatie`). **Onzeker:** de bron daarvoor is het document van 31 mei 2024.
- **Bekostiging:** we filteren niet op de bekostigbaarheid van de student. De regeling gaat over bekostigde *opleidingen*, en het voorbeeld over niet-bekostigde studenten is na de consultatie geschrapt. **Onzeker.**
- **Het label overal:** "Indicatief: berekend op je eigen RO's, niet op het register (ROD) waarmee de Inspectie rekent. Geen oordeel."

## 4. Datastroom

```
Upload (RO/TBG-i, of datamodel/zip uit v4)
  └─ bron.laad_star()                [bestaat; v4 run_auto_pipeline + run_star, ingebouwde sleutel]
       └─ star: fact_inschrijving_schooljaar, fact_inschrijving, dim_opleiding, dim_instelling, meta_leveringen
            ├─ stapelcontrole.controleer_stapel()   [bestaat; teksten bijwerken]
            ├─ waarneming.waarneming(star)          → Waarneming (eerste/laatste 1 oktober, gaten, diploma's vanaf)
            ├─ loopbaan.peilmomenten(star)          → persoon × Jaar: gekozen inschrijving van de instelling
            ├─ loopbaan.diplomas(star)              → persoon × diploma: crebo, niveau, leerweg, datum, jaartijdvak
            └─ duur.nominale_duur(star)             [verhuisd uit naar_1cho]
                 └─ analyse.Analyse (dataclass met alles hierboven + rapport)
                      ├─ indicatoren.py   JR/DR/SR per jaartijdvak → driejaarscijfer
                      ├─ cohorten.py      instroom, rendement, uitval, loopbaanstatus
                      └─ historie.py      meldingen bij te weinig historie
                           ├─ app/ (Streamlit)       smbo dashboard
                           └─ cli: smbo staat         → CSV's + meldingen.txt (headless, cron)
```

### Tussenlaag (exacte schema's)

**`peilmomenten`**: één rij per `_persoon_id` × `Jaar` (1-10-`Jaar`), voor elke persoon die op die 1 oktober bij een van de BRIN's een inschrijving heeft (bron: `fact_inschrijving_schooljaar`, alle rijen, niet alleen `_hoofdinschrijving`).

| kolom | type | betekenis |
|---|---|---|
| `_persoon_id` | str | pseudoniem |
| `Jaar` | i32 | jaar van de peildatum 1 oktober (= v4 `Schooljaar`) |
| `BRIN` | str | BRIN van de gekozen inschrijving |
| `Inschrijvingvolgnummer` | str | |
| `Opleidingcode` | str | crebo |
| `Niveau` | i32 of null | 1–4; null als geen bron het niveau kent |
| `Leertraject` | str | BOL/BBL/BOL_DT/EX/OVO/ODT |
| `DatumBegin` | date | begin van de opleiding (voor het cohort) |

Keuze per persoon × Jaar, over alle BRIN's: hoogste niveau (null als laatste), dan laagste crebo, dan recentste `DatumBegin`, dan het hoogste volgnummer. Een persoon die alleen inschrijvingen zonder niveau heeft, staat er wel in (met `Niveau` null). Zo telt hij niet als verlater.

**`diplomas`**: één rij per `_persoon_id` × `Opleidingcode` × `Datum` (bron: `fact_inschrijving`, `DIP_DatumResultaat` niet leeg, uniek gemaakt).

| kolom | type | betekenis |
|---|---|---|
| `_persoon_id` | str | |
| `Opleidingcode` | str | `DIP_Opleidingcode` |
| `Niveau` | i32 of null | van het crebo van het diploma (v4 `vul_niveau_aan`), niet van de inschrijving |
| `Leertraject` | str | van de inschrijving waar het diploma bij hoort |
| `BRIN` | str | |
| `Datum` | date | `DIP_DatumResultaat` |
| `Jaartijdvak` | i32 | `Datum.year` als de maand ≥ 10 is, anders `year - 1` |

**`Waarneming`** (dataclass, per instelling):
- `eerste_jaar`: de eerste 1 oktober die elke BRIN dekt. Dat is het maximum over de BRIN's van de eerste 1 oktober ≥ `min(DatumBeginPeriode)`.
- `laatste_jaar`: de laatste 1 oktober die elke BRIN dekt. Dat is het minimum over de BRIN's van `max(Laatste_peildatum).year`.
- `gaten`: jaren waarvan de 1 oktober in een gat tussen leveringen valt (uit `stapelcontrole._gaten`).
- `diplomas_vanaf`: date, `min(DatumBeginPeriode)` over de RO-leveringen. Een diploma van daarvoor zien we niet.
- `waarneembaar(jaar) -> bool`: `eerste_jaar ≤ jaar ≤ laatste_jaar` en het jaar ligt niet in een gat.
- `reeks(van, tot) -> bool`: alle jaren in [van, tot] zijn waarneembaar.

## 5. Indicatoren: exacte definities

Notatie: `P(t)` = peilmomenten met `Jaar == t`. "Bij de instelling op 1-10-t" = de persoon staat in `P(t)`. "Diploma 2–4" = een rij in `diplomas` met `Niveau ∈ {2,3,4}`. "Populatie" = `Leertraject ∉ {OVO, ODT}` en het niveau van de toegerekende opleiding ∈ {2,3,4}.

### 5.1 Jaarresultaat (JR), jaartijdvak t
- **Gediplomeerden G(t):** personen met ≥ 1 diploma 2–4 met `Jaartijdvak == t`. Het maakt niet uit of ze op 1-10-t ingeschreven waren (toelichting art. 1: ook wie op 2 oktober instroomde). Toegerekend aan de opleiding (crebo, niveau, leerweg) van het **laatste** diploma in t. Iedere persoon telt één keer.
- **Ongediplomeerde instellingsverlaters U(t):** personen in `P(t)` die niet in `P(t+1)` staan en niet in G(t). Toegerekend aan hun opleiding in `P(t)`.
- **Teller** = |G(t)|. **Noemer** = |G(t)| + |U(t)|. Wie blijft zonder diploma, valt erbuiten.
- **Waarneembaar** als `w.reeks(t, t+1)`. Een diploma in jaartijdvak t loopt tot 30-9-(t+1), en die periode valt binnen de dekking als de 1 oktober van t+1 gedekt is.
- **Stapelen:** een n2-diploma in t, daarna verder op n3, telt positief voor n2 in t. Zakt hij in t+1 op n3 weg zonder diploma, dan is hij een ongediplomeerde verlater voor n3 in t+1.
- Bron: regeling art. 1; UWEB art. 4a.2 lid 1a; DUO-toelichting 2024 ((b+d)/(b+c+d)).

### 5.2 Diplomaresultaat (DR), jaartijdvak t
- **Instellingsverlaters V(t):** personen in `P(t)` die niet in `P(t+1)` staan. Toegerekend aan hun opleiding in `P(t)` (de opleiding waaruit ze vertrekken).
- **Gediplomeerde verlaters:** in V(t), met ≥ 1 diploma 2–4 met `Datum` in [1-10-(t-5), 30-9-(t+1)]. Het niveau en het crebo van dat diploma maken niet uit (toelichting art. 2: n3-diploma, daarna n4 zonder diploma, telt positief).
- **Teller** = gediplomeerde verlaters. **Noemer** = |V(t)|.
- **Waarneembaar** als `w.reeks(t, t+1)`. **Diplomahistorie volledig** als `w.diplomas_vanaf ≤ 1-10-(t-5)`. Is die onvolledig, dan tonen we het cijfer als ondergrens met een melding (§7).
- Bron: regeling art. 2; UWEB art. 4a.2 lid 1b; DUO-toelichting 2024 (d/(c+d)).

### 5.3 Startersresultaat (SR), jaartijdvak t
- **Nieuw ingeschreven N(t):** personen in `P(t)` die op geen van de voorgaande zes 1 oktobers (t-6 … t-1) in `P` staan. Toegerekend aan hun opleiding in `P(t)`.
  - **Terugblik** k = `min(6, t − w.eerste_jaar)`. We kijken alleen naar de waarneembare jaren t-k … t-1. Vereist is k ≥ 1. Bij k < 6 krijgt het cijfer een kolom `Terugblik = k` en een melding (§7).
- **Teller:** in N(t), met een diploma 2–4 met `Jaartijdvak == t`, **of** op 1-10-(t+1) in `P(t+1)` met `Niveau ∈ {2,3,4}`.
- **Noemer** = |N(t)|.
- **Waarneembaar** als `w.reeks(t-k, t+1)` met k ≥ 1.
- **Opstromen zonder diploma** (n2 → n3) blijft bij de instelling: positief. **Afstromen naar entree** op 1-10-(t+1): niet positief, want je moet ingeschreven blijven op niveau 2–4. **Wisselen** binnen de instelling: positief (toelichting art. 3).
- Bron: regeling art. 3 (lid 2: zes voorgaande peildata); UWEB art. 4a.2 lid 1c.

### 5.4 Driejaarscijfer en norm
- Voor jaartijdvak t (het laatste van de drie) en een groep g: Teller = Σ teller(g, t-2..t), Noemer = Σ noemer(g, t-2..t).
- Alleen als **alle drie** de jaartijdvakken waarneembaar zijn voor die indicator. Een jaar met 0 studenten in g telt mee als 0/0.
- Kolommen: `Periode` ("2021-2022 t/m 2023-2024"), `Teller`, `Noemer`, `Percentage` (1 decimaal), `Norm` (voldoende, per niveau), `Onder_norm` (bool, null zonder niveau), `Te_klein` (`Noemer < 12`, onzeker, zie §3), `Volledig` (DR: diplomahistorie; SR: terugblik 6).
- Bij `Te_klein` toont de app geen percentage, maar "te weinig studenten (n = …)".
- Boven niveau (instelling) geldt geen norm. De app toont daar geen norm.

### 5.5 Cohorten (eigen indicatoren, geen Inspectie)
- **Instroomcohort** (persoon, opleiding = crebo × leerweg, cohort t): de eerste `Jaar` waarop de persoon in `P` met dit crebo staat, mits `eerste_peiljaar(DatumBegin) == t`. Begon de opleiding vóór de eerste waarneembare 1 oktober, dan valt de persoon buiten de cohorten (links afgekapt).
- **Herkomst** van de instromer:
  - nieuw bij de instelling (SR-definitie, met dezelfde terugblik);
  - na een diploma bij de instelling (stapelaar);
  - van een ander niveau zonder diploma (opgestroomd of afgestroomd);
  - van een ander crebo op hetzelfde niveau zonder diploma (wissel).
- **Instroom** = het aantal instroomcohort-rijen per opleiding × cohort, uitgesplitst naar herkomst.
- **Rendement nominaal:** een diploma bij de instelling met `Niveau ≥ instroomniveau`, met `Datum ≤ 30-9-(t + duur)`. Daarbij is `duur` = `nominale_duur` (opleiding × leerweg), anders de standaardduur per niveau.
  - **Nominaal + 1:** `Datum ≤ 30-9-(t + duur + 1)`.
  - Waarneembaar als `w.reeks(t, t + duur)` (resp. `+ 1`). Anders "nog niet waarneembaar", en dan telt het niet mee in het percentage (zoals `staat1cho`).
  - We tonen ook "waarvan in de eigen opleiding" (zelfde crebo).
  - Een diploma op een lager niveau (afstromen) telt niet mee voor het rendement. Het staat in de loopbaanstatus.
- **Uitval na x jaar** (x = 1 en x = duur): op 1-10-(t+x) niet in `P`, en geen mbo-diploma (elk niveau, entree inbegrepen) met `Datum` in [1-10-t, 30-9-(t+x-1)]. Waarneembaar als `w.reeks(t, t+x)`.
  - Dit is een **status op dat moment**. Wie terugkomt, is op dat moment niet uitgevallen.
  - Anders dan `staat1cho` (cumulatief, op de laatste inschrijving), maar consistent met SR en DR: uitval na 1 jaar ≈ 1 − SR voor nieuwe instromers.
- **Loopbaanstatus na k jaar** (k = 1, 2, 3), één categorie per cohortrij, op 1-10-(t+k):
  1. Diploma, verder op een hoger niveau (**gestapeld**)
  2. Diploma, vertrokken
  3. Diploma, nog ingeschreven op hetzelfde of een lager niveau
  4. Zonder diploma, zelfde opleiding (zelfde crebo of zijn opvolger)
  5. Zonder diploma, ander crebo op hetzelfde niveau (**studiewissel**)
  6. Zonder diploma, hoger niveau (**opgestroomd**)
  7. Zonder diploma, lager niveau, entree inbegrepen (**afgestroomd**)
  8. Vertrokken zonder diploma (**uitgevallen**)
  9. Nog niet waarneembaar

  "Diploma" = een mbo-diploma bij de instelling sinds 1-10-t, vóór 1-10-(t+k).
- **Studiewissel** = categorie 5. Stapelen (1) en op- of afstromen (6, 7) zijn géén wissel. Daarmee is aan de voorwaarde in de issue voldaan.
  - Een crebo-vernieuwing (`Opleiding_opvolger` in `dim_opleiding`) telt als dezelfde opleiding. **Onzeker:** hoe goed `Opleiding_opvolger` gevuld is. Dat checken we in taak 10.

## 6. Stapelen, opstromen en afstromen: overzicht

| Pad | JR | DR | SR | Cohort/loopbaan |
|---|---|---|---|---|
| n1 → diploma → n2 | entree buiten JR; n2 vanaf daar normaal | entree-diploma telt niet (niveau 2–4) | n2-instroom is niet nieuw (was al ingeschreven) | n2-cohort, herkomst "na diploma" |
| n2 diploma → n3, n3 diploma | n2 positief in t, n3 positief later | positief bij vertrek | n3 niet nieuw | n2: status 1; n3: rendement |
| n2 diploma → n3, n3 uitval | n2 positief; n3 negatief in het vertrekjaar | **positief** voor n3 (diploma n2 ≤ 5 jaar) | n3 niet nieuw | n3: status 8; DR toont het verschil |
| n2 → n3 zonder diploma (opstromen) | zolang ingeschreven buiten JR | pas bij vertrek | positief als starter | n2: status 6; n3-cohort, herkomst "zonder diploma" |
| n3 → n2 zonder diploma (afstromen) | buiten JR tot diploma of vertrek | idem | positief (blijft op 2–4) | n3: status 7 |
| n2 → entree (afstromen) | buiten JR | idem | **negatief** (niet op 2–4) | n2: status 7 |
| wissel binnen niveau | buiten JR | idem | positief | status 5 |
| overstap naar een andere eigen BRIN | buiten JR | geen verlater | positief | volgt opleiding |

## 7. Meldingen bij te weinig historie (`historie.py`)

Wat elke indicator aan 1 oktobers nodig heeft (aaneengesloten, zonder gaten):

| Indicator | Eén jaartijdvak t | Driejaarscijfer (t-2..t) | Volledig |
|---|---|---|---|
| JR | t, t+1 | 4 × 1 oktober | 4 |
| DR | t, t+1; diploma's vanaf 1-10-(t-5) | 4 × 1 oktober | diploma's vanaf 1-10-(t-7): ~9 jaar RO's |
| SR | t-1 … t+1 (k ≥ 1) | 5 × 1 oktober | t-8 … t+1: 10 × 1 oktober (5 RO's) |
| Rendement nominaal + 1 (niveau 4, duur 4) | cohort t … t+5 | n.v.t. | 6 × 1 oktober |

Meldingen (`historie.meldingen(w) -> list[Melding]`, met `ernst` = info/waarschuwing). Bij een melding die afhangt van de data vullen we de getallen in:
- "Jaarresultaat: nog geen driejaarscijfer. Je hebt {n} aaneengesloten 1 oktobers, er zijn er minstens 4 nodig."
- "Diplomaresultaat: diploma's van vóór {datum} zitten niet in je bestanden. Voor {jaren} ontbreken diploma's uit de 5 jaar terug; daar is het cijfer een ondergrens. Upload oudere RO's voor een volledig cijfer."
- "Startersresultaat: we kijken {k} jaar terug in plaats van 6. Wie {k+1}–6 jaar geleden al eens bij je stond en terugkomt, telt als nieuwe student."
- "Rendement nominaal + 1 voor niveau 4 is pas te zien vanaf cohort {jaar}."
- Als een gat de reeks breekt: "Door het gat tussen {na} en {voor} ontbreken de cijfers van {jaren}."
- Is `laatste_jaar` niet voor alle BRIN's gelijk, dan rekenen we tot het vroegste einde (dat staat al in `stapelcontrole._ongelijk_einde`; de tekst wordt: "… we rekenen tot {jaar}").

De oude melding "minder dan 5 schooljaren; rendement na 5 jaar is nog niet te zien" (`stapelcontrole._MIN_JAREN`) vervalt. In de plaats komen de meldingen per indicator.

## 8. Schermen

Streamlit, `layout="wide"`, `st.navigation` in de zijbalk, zoals de v4-app. Grafieken in Altair, tabellen met `st.dataframe(hide_index=True)`. Elke grafiek heeft een `help`-tekst met de definitie (v4-stijl, `_chart_docs`). In de zijbalk staan de filters, die op alle pagina's gelden: niveau, leerweg, domein en opleiding.

1. **Start (bestanden).**
   - `st.file_uploader(accept_multiple_files=True)` voor RO/TBG-i, of een datamodel als zip/parquet.
   - Knop **Samenvoegen** en knop **Probeer met demodata**.
   - Daaronder de meldingen van `Stapelrapport` en `historie`: "Gelukt", BRIN's, jaren, aantal studenten, "Let op: …".
   - Uploads gaan naar een tijdelijke werkmap buiten de repo, zoals `_invoer.synchroniseer_selectie` in v4. Die code is niet te importeren (v4 `app/` zit niet in het wheel), dus we nemen het patroon over in `app/invoer.py`.
   - Pseudonimiseren: met de ingebouwde sleutel van deze repo (besluit 2026-10-14). We bieden niet de keuze "identifiers behouden" van v4. Eén regel tekst: "Persoonsnummers worden vervangen door een code; behandel alles als persoonsgegevens."
2. **Studiesucces (Inspectie-indicatoren).**
   - Tegels per indicator: het driejaarscijfer van de instelling, de laatste periode en n.
   - Tabel per opleiding (crebo × niveau × leerweg, inklapbaar naar niveau) met JR, DR en SR, n, de norm, een neutrale markering "onder norm" en een icoon "onvolledig".
   - Een tijdlijn per indicator (driejaarscijfers per periode) met de normlijn per niveau.
   - Bovenaan een vaste melding: "Indicatief, op je eigen RO's. Geen inspectieoordeel." Geen oordeel "voldoende/onvoldoende studiesucces" en geen 2-van-3-regel.
3. **Cohorten.**
   - Instroom per cohort (gestapelde staaf naar herkomst).
   - Rendement nominaal en nominaal + 1 per cohort, waarbij "nog niet waarneembaar" grijs is.
   - Uitval na 1 jaar en na de nominale duur.
   - Tabel per opleiding met de nominale duur en of die "uit de geplande einddatum" of de "standaardduur" komt.
4. **Loopbanen (stapelen).**
   - Per cohort en niveau een 100%-staaf van de loopbaanstatus na 1 jaar, na de nominale duur en na de nominale duur + 1 (9 categorieën, vaste kleuren). Vaste jaren (1, 2, 3) werken niet: na 1 jaar heeft alleen entree een diploma.
   - Een matrix van het niveau op 1-10-t naar het niveau op 1-10-(t+1) (n1 → n2 enz.), met en zonder diploma.
   - Een korte tekst per categorie.
5. **Over de cijfers.**
   - De definities uit §5 in gewone taal, met bronlinks.
   - De verschillen met de Inspectie (ROD vs RO, de selectie van de inschrijving, de bestuursafbakening) en met de v4-proxy.
   - De dekking: tabel indicator × jaar (waarneembaar, volledig).
   - De meldingen.

Downloads: per tabel `st.download_button` (CSV, alleen geaggregeerd). Geen lijsten op studentniveau.

## 9. Wat er van de bestaande code blijft en wat weg kan

| Bestand | Lot |
|---|---|
| `bron.py` | **Blijft** zoals het is (invoer, zip, GRONDSLAG-weigering, ingebouwde sleutel). |
| `stapelcontrole.py` | **Blijft.** De teksten over staat1cho gaan eruit, net als de melding `_MIN_JAREN` (vervangen door `historie.py`). `_gaten` gaat ook naar `Waarneming`. |
| `naar_1cho.py` | **Weg.** Eerst verhuizen: `nominale_duur`, `opleidingen_met_standaardduur`, `STANDAARDDUUR` en `MIN_INSCHRIJVINGEN_DUUR` naar `duur.py`; `eerste_peiljaar` en `diplomajaar` (→ `jaartijdvak`) naar `loopbaan.py`. De keuze van de hoofdinschrijving wordt `loopbaan.peilmomenten`. |
| `samenvoegen.py` | **Herschrijven:** invoer → `Analyse` + `meldingen.txt` + `stapelcontrole.json` (geen 1CHO-CSV). |
| `r.py`, `r/staat.R`, `r/dashboard.R`, `tests/test_r.py` | **Weg** (de R-brug), als laatste stap zodra het dashboard staat. Tot die tijd blijft de huidige versie werken (issue). |
| `cli.py` | `dashboard` → Streamlit; `staat` → Python-indicatoren naar CSV; `samenvoegen` blijft (Analyse-parquet + meldingen). |
| `scripts/maak_demodata.py` | **Uitbreiden** (taak 21). |
| `demo-video/` | Scènes opnieuw voor de Streamlit-app (taak 23). |
| `tests/test_naar_1cho.py` | Tests voor duur, peiljaar en diplomajaar verhuizen mee; de rest gaat weg. |
| `docs/superpowers/specs|plans/2026-10-14-*` | Blijven als geschiedenis, met bovenaan een verwijzing naar dit ontwerp. |

Nieuwe modules: `waarneming.py`, `loopbaan.py`, `duur.py`, `indicatoren.py`, `cohorten.py`, `historie.py`, `analyse.py`, `app/` (`main.py`, `start.py`, `studiesucces.py`, `cohorten.py`, `loopbanen.py`, `over.py`, `invoer.py`, `ui.py`).

Afhankelijkheden: `streamlit>=1.40` expliciet in `pyproject.toml` (komt nu al via v4 mee). Altair komt mee met Streamlit. R, Rscript en `staat1cho` verdwijnen uit de README.

## 10. Buiten de scope

- Kansengelijkheid (vooropleiding en herkomst ontbreken in de mbo-bestanden).
- Een inspectieoordeel: geen 2-van-3-regel, geen maatwerk, geen "hoog".
- Een benchmark tussen instellingen; een landelijke vergelijking (DUO en de MBO Raad publiceren die al).
- Het Excel-benchmarkrapport en de privacydrempel van `staat1cho` (alleen n < 12 → geen percentage).
- VSV, entree-indicatoren (v4 heeft die al), BPV, examens, bekostiging.
- Doorstroom naar hbo of naar een andere mbo-instelling (niet in de RO's).
- Lijsten of drill-down op studentniveau.
- De indicatorlogica naar v4 overbrengen (open vraag 1; eventueel een vervolgissue).

## 11. Overlap met wat er al is

- **DUO** publiceert per instelling JR en DR (de toelichting van GJ mbo 2024). De Inspectie rekent per opleiding op het ROD. Instellingen zien die cijfers (achteraf, meestal een jaar later).
- **De MBO Raad** maakt de benchmark studiesucces per sector en instelling.
- **Onze meerwaarde:** het staat direct klaar uit je eigen RO's (het lopende jaar inbegrepen), per crebo × leerweg, met cohorten en loopbanen (stapelen) die de officiële cijfers niet laten zien.
- **Onzeker:** welke portals instellingen precies gebruiken en hoe vers die zijn. Dat nemen we mee in het gesprek met de instellingen (issue punt 5).

## 12. Open vragen voor de gebruiker

1. **Waar komt de regeling-logica?** In deze repo (aanbevolen, snel) met een upstream-issue in v4 over de JR-noemer en het jaartijdvak? Of eerst in v4 als publieke `indicatoren`-functies?
2. **Instelling = alle geüploade BRIN's (bestuur)?** De regeling rekent per instelling. Moeten we bij een bestuur met meerdere instellingen per BRIN kunnen rekenen (schakelaar)?
3. **Opleiding = crebo**, met crebo-vernieuwingen via `Opleiding_opvolger` samengenomen? Of liever per kwalificatiedossier?
4. **Normweergave:** een normlijn en een neutrale markering "onder norm" per indicator, zonder gecombineerd oordeel. Is dat oké, of liever helemaal geen norm?
5. **1CHO-export en R** gaan in deze pitch helemaal weg (aanbevolen). Of houden we `smbo samenvoegen --1cho` nog één versie?
6. **Branch:** de pitch-branch (`c7645e6`, 9 commits niet in `main`) eerst naar `main`? Of bouwen we hierop verder in een nieuwe branch?
7. **Demodata naar 10 jaar (5 RO's)**, zodat SR en DR ook "volledig" te zien zijn? Commit `e3e5a74` bracht het terug naar 6 jaar en minder dan 2000 studenten.
8. **Minimale noemer 12** (v4/Inspectie-document, onzeker): aanhouden?
9. **Toets op echte data en het gesprek met instellingen:** welke instelling, en wie regelt het?

## Besluiten op de open vragen (Opus namens Aslam, 2026-11-04)
1. Rekenlogica in deze repo. Melding aan v4 over de jaarresultaat-noemer komt later als issue (niet door de agent).
2. Alle geüploade BRIN's samen = één instelling (bestuur). Geen per-BRIN-rekening in deze ronde.
3. Opleiding = crebo, vernieuwingen samengenomen via `Opleiding_opvolger` waar gevuld.
4. Normlijn tonen, neutraal gelabeld ("norm Regeling studiesucces mbo"), geen "onder norm"-oordeel, en alles gelabeld als indicatief.
5. 1CHO-export en R gaan helemaal weg.
6. Verder bouwen op branch `aslamht/mbo-dashboard` (vertrekt van c7645e6, bestaat al). Niets vragen.
7. Demodata uitbreiden naar 10 jaar (5 RO's), < 2000 studenten blijft.
8. Minimale noemer 12 aanhouden.
9. Echte data: T20 doet Aslam zelf later; agents slaan T20 over.
