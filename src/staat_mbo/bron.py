"""Invoer inlezen: ruwe RO/TBG-i-bestanden of de star van mbo-bekostiging-bestanden."""

import json
import os
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import polars as pl
from mbo_bekostiging_bestanden.identiteit import laad_pseudonimisering_salt
from mbo_bekostiging_bestanden.pipeline import (
    detect_bestandstype,
    run_auto_pipeline,
    run_star,
)
from mbo_bekostiging_bestanden.quality import KwaliteitsFout

VEREISTE_TABELLEN = (
    "fact_inschrijving_schooljaar",
    "fact_inschrijving",
    "dim_deelnemer",
    "dim_opleiding",
    "dim_instelling",
    "meta_leveringen",
)
_SALT = "MBO_PSEUDONIMISERING_SALT"
## Vaste sleutel voor pseudonimiseren, zodat gebruikers niets hoeven in te
## stellen en elke run dezelfde pseudoniemen geeft. Bewuste keuze: de sleutel
## is publiek, dus de uitvoer blijft persoonsgegevens. Een eigen sleutel via
## MBO_PSEUDONIMISERING_SALT gaat voor.
INGEBOUWDE_SLEUTEL = "staat-van-onderwijsinstelling-mbo-v1"


class InvoerFout(Exception):
    """Fout in de invoer, met een tekst voor de gebruiker."""


def _eerste_regel(e: Exception) -> str:
    return str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__


def _bestanden(invoer: list[Path], werkmap: Path) -> list[Path]:
    """Alle bestanden uit de invoer: mappen doorzocht, zips uitgepakt."""
    gevonden: list[Path] = []
    for pad in invoer:
        if not pad.exists():
            raise InvoerFout(f"Bestand of map niet gevonden: {pad}")
        if pad.is_dir():
            gevonden += [p for p in sorted(pad.rglob("*")) if p.is_file()]
        elif pad.suffix.lower() == ".zip":
            doel = werkmap / "zip" / pad.stem
            try:
                with zipfile.ZipFile(pad) as z:
                    z.extractall(doel)
            except zipfile.BadZipFile as e:
                raise InvoerFout(f"{pad.name}: geen geldig zipbestand.") from e
            gevonden += [p for p in sorted(doel.rglob("*")) if p.is_file()]
        else:
            gevonden.append(pad)
    return gevonden


def _lees_parquet(bestanden: list[Path]) -> dict[str, pl.DataFrame]:
    star = {
        p.stem: pl.read_parquet(p) for p in bestanden if p.suffix.lower() == ".parquet"
    }
    ontbrekend = [t for t in VEREISTE_TABELLEN if t not in star]
    if ontbrekend:
        raise InvoerFout(
            "Het datamodel is niet compleet of komt van een oudere versie van "
            "mbo-bekostiging-bestanden. Ontbreekt: "
            + ", ".join(ontbrekend)
            + ". Maak het datamodel opnieuw met de nieuwste versie, of upload de "
            "ruwe RO-bestanden."
        )
    return star


def _kwaliteitsfouten(doel: Path) -> list[str]:
    """De fouten uit ``diagnose/quality.json`` van mbo-bekostiging-bestanden."""
    try:
        q = json.loads((doel / "diagnose" / "quality.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [str(f) for f in q.get("errors", [])]


def _controleer_ruwe_bestanden(bestanden: list[Path]) -> None:
    for b in bestanden:
        soort = detect_bestandstype(b)
        if soort == "grondslag":
            raise InvoerFout(
                f"{b.name}: GRONDSLAG-bestanden gebruiken we niet. "
                "Upload alleen RO en TBG-i."
            )
        if soort is None:
            raise InvoerFout(
                f"{b.name}: onbekend bestand. De naam moet beginnen met RO_ of TBGI_."
            )
    if not any(detect_bestandstype(b) == "ro" for b in bestanden):
        raise InvoerFout("Geen RO-bestand gevonden. Upload minstens één RO.")


@contextmanager
def _sleutel() -> Iterator[None]:
    """Gebruik de ingebouwde sleutel als er geen eigen sleutel is gezet.

    mbo-bekostiging-bestanden onthoudt de sleutel per proces; die cache wordt
    geleegd zodat steeds de juiste sleutel geldt.
    """
    ingebouwd = not os.environ.get(_SALT)
    if ingebouwd:
        os.environ[_SALT] = INGEBOUWDE_SLEUTEL
    laad_pseudonimisering_salt.cache_clear()
    try:
        yield
    finally:
        if ingebouwd:
            del os.environ[_SALT]
        laad_pseudonimisering_salt.cache_clear()


def _bouw_star(bestanden: list[Path], werkmap: Path) -> dict[str, pl.DataFrame]:
    _controleer_ruwe_bestanden(bestanden)
    with _sleutel():
        return _verwerk(bestanden, werkmap)


def _verwerk(bestanden: list[Path], werkmap: Path) -> dict[str, pl.DataFrame]:
    brondata = []
    for b in bestanden:
        doel = werkmap / "brondata" / b.stem
        try:
            run_auto_pipeline(b, doel)
        except KwaliteitsFout as e:
            fouten = _kwaliteitsfouten(doel)
            reden = "; ".join(fouten[:3]) if fouten else _eerste_regel(e)
            soort = "RO" if detect_bestandstype(b) == "ro" else "TBG-i-bestand"
            raise InvoerFout(
                f"{b.name}: de kwaliteitscontrole keurt dit bestand af. Reden: "
                f"{reden}. Is het bestand bewerkt of afgebroken? Vraag dan een "
                f"nieuw {soort} aan bij DUO."
            ) from e
        except ValueError as e:
            raise InvoerFout(
                f"{b.name}: kan dit bestand niet lezen. Is het een echt DUO-bestand? "
                f"({_eerste_regel(e)})"
            ) from e
        brondata.append(doel)
    try:
        run_star(brondata, werkmap / "star", scenario="smbo")
    except (KwaliteitsFout, ValueError) as e:
        fouten = _kwaliteitsfouten(werkmap / "star")
        reden = "; ".join(fouten[:3]) if fouten else _eerste_regel(e)
        raise InvoerFout(
            f"Samenvoegen mislukt bij de kwaliteitscontrole. Reden: {reden}."
        ) from e
    return _lees_parquet(sorted((werkmap / "star" / "datamodel").glob("*.parquet")))


def laad_star(invoer: list[Path], werkmap: Path) -> dict[str, pl.DataFrame]:
    """Lees de invoer als star-tabellen.

    Args:
        invoer:  Ruwe RO/TBG-i-bestanden, een ``datamodel/``-map, losse
                 parquetbestanden of een zip met een van beide.
        werkmap: Map voor tussenbestanden.
    """
    werkmap.mkdir(parents=True, exist_ok=True)
    bestanden = _bestanden(invoer, werkmap)
    if not bestanden:
        raise InvoerFout("Geen bestanden gevonden.")
    parquet = [b for b in bestanden if b.suffix.lower() == ".parquet"]
    if any(b.stem in VEREISTE_TABELLEN for b in parquet):
        return _lees_parquet(parquet)
    if parquet:
        raise InvoerFout(
            f"{parquet[0].name}: dit is geen RO, TBG-i of datamodel van "
            "mbo-bekostiging-bestanden. Upload de ruwe RO-bestanden, of de map "
            "datamodel."
        )
    return _bouw_star(bestanden, werkmap)
