"""Neem de demovideo op: uploaden, samenvoegen, dashboard.

Start eerst de app met demodata (zie demo-video/README.md), dan:
    uv run --group demo python demo-video/scenes/record.py
Schrijft scenes/take.webm en scenes/tijden.json (start van elke stap).
In de pagina staat alleen een kader om het uitgelegde element; de ondertitels
komen in een balk onder de video (stitch.py), zodat niets wordt afgedekt.
Raakt een kader een ander element, dan stopt de opname met een fout.
"""

import json
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

DEMO = Path(__file__).parent.parent

RAW = Path(__file__).parent
RUW = DEMO.parent / "demodata"
APP_URL = "http://127.0.0.1:8791"
VIEWPORT = {"width": 1280, "height": 720}
DUREN = json.loads((DEMO / "audio" / "duren.json").read_text())
RING_JS = (RAW / "ring.js").read_text(encoding="utf-8")
LEEG_JS = "() => document.querySelectorAll('.__a').forEach(e => e.remove())"
## Elementen die een kader niet mag raken.
ELEMENTEN = (
    "button, a, input, label, select, .nav-link, .card, .card-header, "
    ".bslib-value-box, .shiny-input-container, .js-plotly-plot, h1, h2, h3, h4, "
    "p, li, table, .dashboard-header, .upload-hint, .progress"
)
KLEUR = {"blauw": "#2563eb", "groen": "#16a34a", "oranje": "#ea580c"}


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
    """Wacht tot Shiny klaar is met rekenen."""
    page.wait_for_function(
        "() => !document.documentElement.classList.contains('shiny-busy')",
        timeout=timeout,
    )
    time.sleep(0.8)


def box(locs):
    bs = [lc.bounding_box() for lc in locs]
    links = min(b["x"] for b in bs)
    boven = min(b["y"] for b in bs)
    rechts = max(b["x"] + b["width"] for b in bs)
    onder = max(b["y"] + b["height"] for b in bs)
    return {"x": links, "y": boven, "width": rechts - links, "height": onder - boven}


def klik(page, loc):
    b = loc.bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, steps=18)
    time.sleep(0.3)
    loc.click()


class Opname:
    def __init__(self, page):
        self.page = page
        self.t0 = time.monotonic()
        self.tijden = {}

    def stap(self, naam, target, kleur="blauw", actie=None):
        """Kader om het element; houd vast zolang de voice-over duurt."""
        locs = target if isinstance(target, list) else [target]
        locs[0].evaluate("e => e.scrollIntoView({block:'center'})")
        time.sleep(0.5)
        geraakt = self.page.evaluate(
            RING_JS,
            {"box": box(locs), "kleur": KLEUR[kleur], "selectors": ELEMENTEN},
        )
        if geraakt:
            raise RuntimeError(f"Kader van '{naam}' raakt andere elementen: {geraakt}")
        self.tijden[naam] = time.monotonic() - self.t0
        time.sleep(DUREN[naam] + 0.7)
        self.page.evaluate(LEEG_JS)
        if actie:
            actie()


def neem_op(page):
    o = Opname(page)
    page.goto(APP_URL)
    page.wait_for_selector("#btn_samenvoegen", timeout=90000)
    rustig(page)
    o.tijden["_klaar"] = time.monotonic() - o.t0

    o.stap(
        "intro",
        page.locator(".upload-card"),
    )
    page.set_input_files("#bron_upload", sorted(str(p) for p in RUW.iterdir()))
    page.wait_for_selector("text=Upload complete", timeout=60000)
    invoerveld = page.locator(
        ".shiny-input-container", has=page.locator("#bron_upload")
    )
    o.stap(
        "bestanden",
        invoerveld.first,
    )
    knop = page.locator("#btn_samenvoegen")
    o.stap(
        "samenvoegen",
        knop,
        actie=lambda: klik(page, knop),
    )
    page.wait_for_selector("text=Gelukt", timeout=180000)
    rustig(page)
    o.stap(
        "gelukt",
        page.locator("#voorstap_resultaat_ui > div").first,
        kleur="groen",
    )
    verder = page.locator("#btn_verder")
    o.stap(
        "verder",
        verder,
        actie=lambda: klik(page, verder),
    )
    page.wait_for_selector(".dashboard-header", timeout=180000)
    rustig(page)
    time.sleep(4)

    tabs = page.locator(
        "ul.nav", has=page.locator(".nav-link", has_text="Rendement")
    ).first
    o.stap("tabs", tabs)
    klik(page, page.locator(".nav-link", has_text="Rendement").first)
    rustig(page)
    time.sleep(2)
    page.locator("#kpi_rend3 .bslib-value-box").wait_for(timeout=60000)
    o.stap(
        "rendement",
        [page.locator(f"#kpi_rend{j} .bslib-value-box") for j in (3, 5, 8)],
    )
    klik(page, page.locator(".nav-link", has_text="Uitval").first)
    rustig(page)
    time.sleep(2)
    page.locator("#kpi_uitval_kpi .bslib-value-box").wait_for(timeout=60000)
    kpis = ["#kpi_uitval_kpi", "#kpi_uitval1", "#kpi_uitval3"]
    o.stap(
        "uitval",
        [page.locator(f"{k} .bslib-value-box") for k in kpis],
    )
    bol = page.locator("#vorm_filter label", has_text="BOL").first
    o.stap(
        "filter",
        page.locator("#vorm_filter"),
        kleur="oranje",
        actie=lambda: klik(page, bol),
    )
    rustig(page)
    time.sleep(1.5)
    ## De knop staat in de vaste kopbalk; scrol terug zodat er niets onder ligt.
    page.evaluate("() => window.scrollTo({top: 0})")
    time.sleep(0.8)
    o.stap("slot", page.locator("#btn_opnieuw"))
    time.sleep(1.0)
    return o


def main():
    wacht_op_app()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        warm = browser.new_page()
        warm.goto(APP_URL)
        warm.wait_for_selector("#btn_samenvoegen", timeout=90000)
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
