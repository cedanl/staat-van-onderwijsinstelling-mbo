"""Commando ``smbo``: samenvoegen, staat berekenen, dashboard starten."""

import argparse
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smbo",
        description="Staat van de Onderwijsinstelling voor het MBO",
    )
    sub = parser.add_subparsers(dest="commando", required=True)

    p = sub.add_parser(
        "samenvoegen",
        help="Voeg RO/TBG-i-bestanden of een datamodel samen tot één 1CHO-bestand",
    )
    p.add_argument(
        "invoer",
        nargs="+",
        type=Path,
        help="Ruwe bestanden, een datamodel-map, parquetbestanden of een zip",
    )
    p.add_argument("--uitvoer", type=Path, required=True, help="Map voor de uitvoer")

    p = sub.add_parser("staat", help="Bereken de indicatoren zonder dashboard (R)")
    p.add_argument("bestand", type=Path, help="1cho_mbo.csv uit 'smbo samenvoegen'")
    p.add_argument("--uitvoer", type=Path, required=True, help="Map voor de uitvoer")

    sub.add_parser("dashboard", help="Start het dashboard in de browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    raise NotImplementedError(args.commando)
