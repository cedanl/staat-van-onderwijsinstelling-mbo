"""Neem de demovideo op: start, demodata, Studiesucces, Cohorten, Loopbanen, Over.

Start eerst de app (zie demo-video/README.md), dan:
    uv run --group demo python demo-video/scenes/record.py
Schrijft scenes/take.webm en scenes/tijden.json (start van elke stap).
In de pagina staat alleen een kader om het uitgelegde element; de ondertitels
komen in een balk onder de video (stitch.py), zodat niets wordt afgedekt.
Raakt een kader een ander element, dan stopt de opname met een fout.
"""

import json
import os
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

DEMO = Path(__file__).parent.parent

RAW = Path(__file__).parent
APP_URL = f"http://127.0.0.1:{os.environ.get('STAAT_MBO_POORT', '8599')}"
VIEWPORT = {"width": 1280, "height": 720}
DUREN = json.loads((DEMO / "audio" / "duren.json").read_text())
RING_JS = (RAW / "ring.js").read_text(encoding="utf-8")
LEEG_JS = "() => document.querySelectorAll('.__a').forEach(e => e.remove())"
## Elementen die een kader niet mag raken.
ELEMENTEN = (
    "button:not([data-testid='stBaseButton-elementToolbar']), a:not([href^='#']), input, label, h1, h2, h3, p, li, "
    "[data-testid='stMetric'], [data-testid='stAlert'], "
    "[data-testid='stDataFrame'], [data-testid='stVegaLiteChart'], "
    "[data-testid='stFileUploader'], [data-testid='stSidebarNav']"
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

    def stap(self, naam, target, kleur="blauw", actie=None, pad=4, rand=3):
        """Kader om het element; houd vast zolang de voice-over duurt."""
        locs = target if isinstance(target, list) else [target]
        locs[0].evaluate("e => e.scrollIntoView({block:'center'})")
        time.sleep(0.4)
        ## Zet het hele kader in beeld: gecentreerd, of bovenaan als het te hoog is.
        b = box(locs)
        doel = 360 - b["height"] / 2 if b["height"] < 560 else 70
        self.page.evaluate(
            "([sel, d]) => document.querySelector(sel).scrollBy(0, d)",
            [HOOFD, b["y"] - doel],
        )
        time.sleep(0.6)
        geraakt = self.page.evaluate(
            RING_JS,
            {
                "box": box(locs),
                "kleur": KLEUR[kleur],
                "selectors": ELEMENTEN,
                "pad": pad,
                "rand": rand,
            },
        )
        if geraakt:
            raise RuntimeError(f"Kader van '{naam}' raakt andere elementen: {geraakt}")
        self.tijden[naam] = time.monotonic() - self.t0
        time.sleep(DUREN[naam] + 0.7)
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


def neem_op(page):
    o = Opname(page)
    page.goto(APP_URL)
    page.get_by_role("heading", name="Staat van de Onderwijsinstelling MBO").wait_for(
        timeout=90000
    )
    rustig(page)
    o.tijden["_klaar"] = time.monotonic() - o.t0

    o.stap("start", page.get_by_test_id("stFileUploader"))
    knop = page.get_by_role("button", name="Probeer met demodata")
    o.stap("demodata", knop, actie=lambda: klik(page, knop))
    page.get_by_text("Gelukt").first.wait_for(timeout=180000)
    rustig(page)
    o.stap("gelukt", page.get_by_test_id("stAlert").first, kleur="groen")

    naar_pagina(page, "Studiesucces")
    hoofd = page.locator(HOOFD)
    grafieken = hoofd.get_by_test_id("stVegaLiteChart")
    o.stap("studiesucces", list(hoofd.get_by_test_id("stMetric").all()))
    o.stap(
        "indicatief",
        hoofd.get_by_test_id("stAlert").first,
        kleur="oranje",
        pad=-2,
        rand=2,
    )
    o.stap("tabel", hoofd.get_by_test_id("stDataFrame").first)
    kopjes = (
        "verloop-per-niveau",
        "jaarresultaat",
        "diplomaresultaat",
        "startersresultaat",
    )
    o.stap(
        "norm",
        [
            *(hoofd.locator(f"#{i}") for i in kopjes),
            *hoofd.get_by_test_id("stVegaLiteChart").all(),
        ],
    )

    naar_pagina(page, "Cohorten")
    o.stap(
        "cohorten",
        [hoofd.locator("#rendement-per-cohort"), grafieken.nth(1)],
    )

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
    page.evaluate("() => window.scrollTo({top: 0})")
    time.sleep(0.8)
    o.stap("slot", page.get_by_test_id("stSidebarNav"))
    time.sleep(1.0)
    return o


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
