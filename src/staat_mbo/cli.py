"""Commando ``smbo``: samenvoegen, staat berekenen, dashboard starten."""

import argparse
import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

STANDAARD_POORT = 8501
## Seconden wachten voordat de browser opent, zodat de server klaar is.
_WACHT_BROWSER = 2.0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smbo",
        description="Staat van de Onderwijsinstelling voor het MBO",
    )
    sub = parser.add_subparsers(dest="commando", required=True)

    for naam, hulp in (
        ("samenvoegen", "Voeg RO/TBG-i-bestanden of een datamodel samen"),
        ("staat", "Bereken de indicatoren en schrijf CSV's, zonder dashboard"),
    ):
        p = sub.add_parser(naam, help=hulp)
        p.add_argument(
            "invoer",
            nargs="+",
            type=Path,
            help="Ruwe bestanden, een datamodel-map, parquetbestanden of een zip",
        )
        p.add_argument(
            "--uitvoer", type=Path, required=True, help="Map voor de uitvoer"
        )

    p = sub.add_parser("dashboard", help="Start het dashboard in de browser")
    p.add_argument(
        "--poort", type=int, default=STANDAARD_POORT, help="Poort (standaard 8501)"
    )
    p.add_argument(
        "--geen-browser", action="store_true", help="Open de browser niet zelf"
    )
    p.add_argument(
        "--invoer",
        type=Path,
        help="Map met bestanden die het dashboard bij de start laadt",
    )
    return parser


def _open_browser(url: str) -> None:
    timer = threading.Timer(_WACHT_BROWSER, webbrowser.open, [url])
    timer.daemon = True
    timer.start()


def _dashboard(poort: int, geen_browser: bool, invoer: Path | None) -> int:
    env = {**os.environ, "STREAMLIT_BROWSER_GATHER_USAGE_STATS": "false"}
    if invoer is not None:
        env["STAAT_MBO_INVOER"] = str(invoer.absolute())
    opdracht = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(Path(__file__).parent / "app" / "main.py"),
        "--server.port",
        str(poort),
        "--server.headless",
        "true",
    ]
    if not geen_browser:
        _open_browser(f"http://localhost:{poort}")
    try:
        return subprocess.run(opdracht, env=env, check=False).returncode
    except KeyboardInterrupt:
        return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.commando == "dashboard":
        return _dashboard(args.poort, args.geen_browser, args.invoer)

    from staat_mbo import samenvoegen

    functie = getattr(samenvoegen, args.commando)
    analyse = functie(args.invoer, args.uitvoer)
    print("\n".join(analyse.regels()))
    return 0 if analyse.ok else 1
