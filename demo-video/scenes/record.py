"""Neem de demovideo op: upload, meldingen, kerncijfers, Studiesucces, Cohorten, Loopbanen, Over.

Start eerst de app zonder --invoer (zie demo-video/README.md), dan:
    uv run --group demo python demo-video/scenes/record.py
De RO-bestanden uit src/staat_mbo/demodata gaan echt via de bestandskiezer naar
binnen. Schrijft scenes/take.webm en scenes/tijden.json (start van elke stap).
In de pagina staan een kader, een pijl en een chip bij het uitgelegde element;
de ondertitels komen in een balk onder de video (stitch.py). Raakt het kader, de
chip of de pijl een ander element, dan stopt de opname met een fout.
STAAT_MBO_SHOTS=<map> bewaart een screenshot per stap; STAAT_MBO_DROOG=1 houdt
elke stap kort vast (alleen om overlap te controleren).
"""

import importlib.util
import json
import os
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

DEMO = Path(__file__).parent.parent
RAW = Path(__file__).parent
_spec = importlib.util.spec_from_file_location("stappen", DEMO / "stappen.py")
_stappen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_stappen)
CHIPS, WAARDEN = _stappen.CHIPS, _stappen.WAARDEN

APP_URL = f"http://127.0.0.1:{os.environ.get('STAAT_MBO_POORT', '8599')}"
VIEWPORT = {"width": 1600, "height": 900}
DEMODATA = sorted((DEMO.parent / "src" / "staat_mbo" / "demodata").glob("RO_*.csv"))
SHOTS = os.environ.get("STAAT_MBO_SHOTS")
DROOG = bool(os.environ.get("STAAT_MBO_DROOG"))
## Maak de pagina smaller: rechts blijft ruimte voor de chip.
STIJL = (
    "[data-testid=stMainBlockContainer]{max-width:none !important;"
    "padding-left:24px !important;padding-right:300px !important;}"
)
INIT_JS = (
    "document.addEventListener('DOMContentLoaded',()=>{"
    "const s=document.createElement('style');"
    f"s.textContent={json.dumps(STIJL)};document.head.appendChild(s);}});"
)
DUREN = json.loads((DEMO / "audio" / "duren.json").read_text())
RING_JS = (RAW / "ring.js").read_text(encoding="utf-8")
LEEG_JS = "() => document.querySelectorAll('.__a,.__ruimte').forEach(e => e.remove())"
## Lege ruimte onderaan de pagina, zodat een element hoog in beeld kan staan en de chip eronder past.
RUIMTE_JS = """() => {
  const b = document.querySelector("[data-testid='stMainBlockContainer'] > [data-testid='stVerticalBlock']");
  const d = document.createElement('div');
  d.className = '__ruimte';
  d.style.height = '600px';
  b.appendChild(d);
}"""
## Elementen die kader, chip en pijl niet mogen raken.
ELEMENTEN = (
    "button:not([data-testid='stBaseButton-elementToolbar']), a:not([href^='#']), input, label, h1, h2, h3, p, li, "
    "[data-testid='stMetric'], [data-testid='stAlert'], [data-testid='stExpander'], "
    "[data-testid='stDataFrame'], [data-testid='stVegaLiteChart'], "
    "[data-testid='stFileUploader'], [data-testid='stSidebarNav'], "
    "[data-testid='stSelectbox'], [data-testid='stMultiSelect'], [data-testid='stRadio']"
)
KLEUR = {"blauw": "#2563eb", "groen": "#16a34a", "oranje": "#ea580c"}
HOOFD = "section[data-testid='stMain']"


def wacht_op_app(timeout=90):
    eind = time.time() + timeout
    while time.time() < eind:
        try:
            urllib.request.urlopen(APP_URL, timeout=2)
            return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"App niet bereikbaar op {APP_URL}")


def rustig(page, timeout=180000):
    """Wacht tot Streamlit klaar is met rekenen en de grafieken getekend zijn."""
    page.wait_for_function(
        "() => !document.querySelector(\"[data-testid='stStatusWidget']\")",
        timeout=timeout,
    )
    time.sleep(1.5)


def box(locs):
    bs = [lc.bounding_box() for lc in locs]
    links = min(b["x"] for b in bs)
    boven = min(b["y"] for b in bs)
    rechts = max(b["x"] + b["width"] for b in bs)
    onder = max(b["y"] + b["height"] for b in bs)
    return {"x": links, "y": boven, "width": rechts - links, "height": onder - boven}


def klik(page, loc):
    loc.scroll_into_view_if_needed()
    b = loc.bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=18)
    time.sleep(0.3)
    loc.click()


class Opname:
    def __init__(self, page):
        self.page = page
        self.t0 = time.monotonic()
        self.tijden = {}

    def stap(self, naam, target, voor=None, actie=None, pad=4, rand=3, scrollen=True):
        """Kader, pijl en chip bij het element; houd vast zolang de voice-over duurt."""
        locs = target if isinstance(target, list) else [target]
        if voor:
            voor()
        ## Muis uit het beeld, anders opent een hulpballon bij een vraagteken.
        self.page.mouse.move(1590, 890)
        if scrollen:
            self.page.evaluate(RUIMTE_JS)
            locs[0].evaluate("e => e.scrollIntoView({block:'center'})")
            time.sleep(0.4)
            ## Zet het hele kader in beeld: gecentreerd, of bovenaan als het te hoog is.
            b = box(locs)
            hoog = VIEWPORT["height"]
            if b["height"] >= hoog - 160:
                doel = 70
            elif b["height"] < 400:
                doel = 220  # hoog in beeld, de chip kan eronder
            else:
                doel = hoog / 2 - b["height"] / 2
            self.page.evaluate(
                "([sel, d]) => document.querySelector(sel).scrollBy(0, d)",
                [HOOFD, b["y"] - doel],
            )
            time.sleep(0.6)
        label, toelichting, kleur = CHIPS.get(naam, (None, None, "blauw"))
        res = self.page.evaluate(
            RING_JS,
            {
                "box": box(locs),
                "kleur": KLEUR[kleur],
                "selectors": ELEMENTEN,
                "pad": pad,
                "rand": rand,
                "label": label,
                "tekst": toelichting,
                "last": locs[-1].element_handle(),
            },
        )
        if res["geraakt"]:
            raise RuntimeError(f"Annotatie van '{naam}' raakt iets: {res['geraakt']}")
        print(f"  {naam}: chip {res['chip']}")
        self.tijden[naam] = time.monotonic() - self.t0
        if SHOTS:
            self.page.screenshot(path=str(Path(SHOTS) / f"{naam}.png"))
        time.sleep(0.5 if DROOG else DUREN[naam] + 0.7)
        self.page.evaluate(LEEG_JS)
        if actie:
            actie()


def naar_pagina(page, naam):
    """Klik de pagina in de zijbalk aan en wacht tot hij getekend is."""
    klik(page, page.get_by_test_id("stSidebarNav").get_by_role("link", name=naam))
    page.get_by_role("heading", name=naam, level=1).wait_for(timeout=60000)
    rustig(page)
    if naam != "Over de cijfers":
        page.locator(f"{HOOFD} [data-testid='stVegaLiteChart']").first.wait_for(
            state="attached", timeout=60000
        )
    time.sleep(1.0)


def tegels(page):
    """De zes kerncijfers op Start (kolom met metric en toelichting), op volgorde."""
    kol = page.locator(f"{HOOFD} [data-testid='stColumn']").filter(
        has=page.locator("[data-testid='stMetric']")
    )
    assert kol.count() == 6, kol.count()
    return [kol.nth(i) for i in range(6)]


def controleer_waarde(naam, tegel):
    """Tekst en beeld moeten kloppen: de waarde uit het script staat echt op de pagina."""
    tekst = tegel.get_by_test_id("stMetric").inner_text()
    if WAARDEN[naam] not in tekst:
        raise RuntimeError(f"{naam}: verwacht {WAARDEN[naam]}, op de pagina: {tekst!r}")


def niveaufilter(page):
    return page.locator("[data-testid='stSidebar'] [data-testid='stMultiSelect']").first


def kies_niveau(page, optie):
    """Kies een niveau in het filter; optie None wist het filter weer."""
    kies = niveaufilter(page)
    if optie is None:
        kies.get_by_label("Clear all").click()
    else:
        klik(page, kies)
        page.get_by_role("option", name=optie, exact=True).click()
        page.keyboard.press("Escape")
    rustig(page)


def neem_op(page):
    o = Opname(page)
    page.goto(APP_URL)
    page.get_by_role("heading", name="Staat van de Onderwijsinstelling MBO").wait_for(
        timeout=90000
    )
    rustig(page)
    o.tijden["_klaar"] = time.monotonic() - o.t0
    hoofd = page.locator(HOOFD)

    o.stap(
        "start",
        [
            hoofd.get_by_role("heading", level=1),
            hoofd.get_by_text("Kies al je RO- en TBG-i-bestanden").first,
        ],
    )
    o.stap("privacy", hoofd.get_by_text("Persoonsnummers worden vervangen").first)

    def upload():
        page.locator("input[type='file']").set_input_files([str(p) for p in DEMODATA])
        page.get_by_text(DEMODATA[0].name[:7]).first.wait_for(timeout=30000)
        time.sleep(1.5)

    o.stap("kies", page.get_by_test_id("stFileUploader"), voor=upload)
    knop = page.get_by_role("button", name="Samenvoegen")
    o.stap("samenvoegen", knop, actie=lambda: klik(page, knop))
    page.get_by_text("Gelukt").first.wait_for(timeout=180000)
    page.get_by_text("Kerncijfers").first.wait_for(timeout=180000)
    rustig(page)
    alerts = hoofd.get_by_test_id("stAlert")
    o.stap(
        "gelukt",
        [alerts.first, hoofd.get_by_test_id("stMarkdown").filter(has_text="BRIN")],
    )
    o.stap("meldingen", [alerts.nth(1), alerts.nth(2)])

    kaarten = tegels(page)
    for i, naam in enumerate(
        ("jaar", "diploma", "starters", "instroom", "uitval", "doorstroom")
    ):
        controleer_waarde(naam, kaarten[i])
        o.stap(naam, kaarten[i], pad=2, rand=3)

    naar_pagina(page, "Studiesucces")
    grafieken = hoofd.get_by_test_id("stVegaLiteChart")
    kaarten = tegels_studiesucces(page)
    for naam, tegel in zip(("jaar", "diploma", "starters"), kaarten, strict=True):
        controleer_waarde(naam, tegel)
    o.stap("indicatoren", kaarten, pad=2)
    o.stap("tabel", hoofd.get_by_test_id("stDataFrame").first)
    o.stap(
        "norm",
        [
            hoofd.locator("#verloop-per-niveau"),
            hoofd.locator("#jaarresultaat"),
            grafieken.first,
        ],
    )
    o.stap(
        "filter",
        niveaufilter(page),
        scrollen=False,
        actie=lambda: kies_niveau(page, "Niveau 4"),
    )
    page.evaluate(
        "() => document.querySelector(\"section[data-testid='stMain']\").scrollTo(0, 0)"
    )
    time.sleep(0.8)
    o.stap(
        "gefilterd",
        tegels_studiesucces(page),
        pad=2,
        actie=lambda: kies_niveau(page, None),
    )

    naar_pagina(page, "Cohorten")
    o.stap(
        "instroomcohort",
        [hoofd.locator("#instroom-per-cohort"), grafieken.first],
    )
    o.stap(
        "rendement",
        [hoofd.locator("#rendement-per-cohort"), grafieken.nth(1)],
    )
    o.stap("uitvalcohort", [hoofd.locator("#uitval"), grafieken.nth(2)])

    naar_pagina(page, "Loopbanen")
    o.stap(
        "loopbanen",
        [hoofd.locator("#loopbaanstatus-na-de-start"), grafieken.first],
    )
    o.stap(
        "niveaus",
        [
            hoofd.locator("#van-niveau-naar-niveau"),
            hoofd.get_by_test_id("stDataFrame").last,
        ],
        pad=0,
        rand=2,
    )

    naar_pagina(page, "Over de cijfers")
    o.stap(
        "over",
        [
            hoofd.locator("#wat-dekken-je-bestanden"),
            hoofd.get_by_test_id("stDataFrame").last,
        ],
        pad=0,
        rand=2,
    )
    page.evaluate(
        "() => document.querySelector(\"section[data-testid='stMain']\").scrollTo(0, 0)"
    )
    time.sleep(0.8)
    o.stap("indicatief", hoofd.get_by_test_id("stAlert").first, pad=-2, rand=2)
    time.sleep(1.0)
    return o


def tegels_studiesucces(page):
    kol = page.locator(f"{HOOFD} [data-testid='stColumn']").filter(
        has=page.locator("[data-testid='stMetric']")
    )
    assert kol.count() == 3, kol.count()
    return [kol.nth(i) for i in range(3)]


def main():
    wacht_op_app()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        warm = browser.new_page()
        warm.goto(APP_URL)
        warm.get_by_role(
            "heading", name="Staat van de Onderwijsinstelling MBO"
        ).wait_for(timeout=90000)
        warm.close()

        ctx = browser.new_context(
            viewport=VIEWPORT, record_video_dir=str(RAW), record_video_size=VIEWPORT
        )
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        o = neem_op(page)
        video = page.video.path()
        ctx.close()
        browser.close()

    doel = RAW / "take.webm"
    doel.unlink(missing_ok=True)
    Path(video).rename(doel)
    (RAW / "tijden.json").write_text(
        json.dumps({"tijden": o.tijden}, indent=2), encoding="utf-8"
    )
    print(json.dumps(o.tijden, indent=2))


if __name__ == "__main__":
    main()
