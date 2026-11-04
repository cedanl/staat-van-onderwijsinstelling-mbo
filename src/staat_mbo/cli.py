"""Commando ``smbo``: samenvoegen, staat berekenen, dashboard starten."""

import argparse
from pathlib import Path


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

    sub.add_parser("dashboard", help="Start het dashboard in de browser")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.commando in ("samenvoegen", "staat"):
        from staat_mbo import samenvoegen

        functie = getattr(samenvoegen, args.commando)
        analyse = functie(args.invoer, args.uitvoer)
        print("\n".join(analyse.regels()))
        return 0 if analyse.ok else 1

    from staat_mbo.r import RFout, draai_r

    try:
        return draai_r("dashboard.R")
    except RFout as e:
        print(e)
        return 1
