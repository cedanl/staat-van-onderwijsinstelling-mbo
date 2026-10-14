"""R aanroepen voor staat1cho (berekenen en dashboard)."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

from staat_mbo.naar_1cho import LABEL_DIPLOMA, SOORT_ONDERWIJS

MIN_STAAT1CHO = (0, 3, 0)
_WINDOWS_R = "C:/Program Files/R"
_INSTALLATIE = (
    'Installeer in R: install.packages("remotes"); '
    'remotes::install_github("cedanl/staat-van-onderwijsinstelling")'
)


class RFout(Exception):
    """R of staat1cho ontbreekt."""


def script_pad(naam: str) -> Path:
    return Path(__file__).parent / "r" / naam


def r_env() -> dict[str, str]:
    """Omgeving voor de R-scripts: welke Python, welk diploma, welk onderwijs."""
    return {
        **os.environ,
        "STAAT_MBO_PYTHON": sys.executable,
        "STAAT_MBO_DIPLOMA": LABEL_DIPLOMA,
        "STAAT_MBO_SOORT": SOORT_ONDERWIJS,
    }


def vind_rscript() -> Path:
    gevonden = shutil.which("Rscript")
    if gevonden:
        return Path(gevonden)
    kandidaten = sorted(Path(_WINDOWS_R).glob("R-*/bin/Rscript.exe"))
    if kandidaten:
        return kandidaten[-1]
    raise RFout("R is niet gevonden. Installeer R: https://cran.r-project.org")


def controleer_staat1cho(rscript: Path) -> None:
    uit = subprocess.run(
        [
            str(rscript),
            "-e",
            (
                'cat(if (requireNamespace("staat1cho", quietly = TRUE)) '
                'as.character(packageVersion("staat1cho")) else "")'
            ),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    versie = uit.stdout.strip()
    if not versie:
        raise RFout(f"Het R-pakket staat1cho ontbreekt. {_INSTALLATIE}")
    if tuple(int(d) for d in versie.split(".")[:3]) < MIN_STAAT1CHO:
        raise RFout(f"staat1cho {versie} is te oud (minimaal 0.3.0). {_INSTALLATIE}")


def draai_r(script: str, *args: str) -> int:
    """Draai een meegeleverd R-script; uitvoer gaat naar de terminal."""
    rscript = vind_rscript()
    controleer_staat1cho(rscript)
    opdracht = [str(rscript), str(script_pad(script)), *args]
    return subprocess.run(opdracht, env=r_env(), check=False).returncode
