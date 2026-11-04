"""Opname knippen tot demo_final.mp4, met ondertitels en zonder geluid.

Elke stap blijft zijn leestijd in beeld vanaf het moment dat hij begint
(scenes/tijden.json). Wachttijd tussen stappen (rekenen, laden) wordt
weggeknipt tot een korte overgang. De ondertitels staan in een balk onder het
beeld van de app, zodat ze nooit iets in de app afdekken.
Aanroep: uv run python demo-video/stitch.py
"""

import json
import subprocess
import sys
import textwrap
from pathlib import Path

DEMO = Path(__file__).parent
sys.path.insert(0, str(DEMO))
from stappen import STAPPEN, leestijd

TAKE = DEMO / "scenes" / "take.webm"
UIT = DEMO / "demo_final.mp4"
NA_STAP = 0.6  # seconden na de leestijd die in beeld blijven (klik, begin van laden)
VOOR_STAP = 1.0  # seconden vóór de volgende stap
EINDE = 2.0
BALK = 120  # hoogte van de ondertitelbalk onder het beeld
LETTER = r"C\:/Windows/Fonts/segoeuib.ttf"
ONDERTITEL = dict(STAPPEN)


tijden = json.loads((DEMO / "scenes" / "tijden.json").read_text())["tijden"]
start = max(0.0, tijden.pop("_klaar") - 0.3)
stappen = [(naam, t, leestijd(ONDERTITEL[naam])) for naam, t in tijden.items()]

## Te bewaren stukken van de opname.
stukken = []
begin = start
for i, (_, t, lees) in enumerate(stappen):
    eind = t + lees + NA_STAP
    if i + 1 < len(stappen):
        volgende = stappen[i + 1][1]
        if volgende - VOOR_STAP > eind:
            stukken.append((begin, eind))
            begin = volgende - VOOR_STAP
    else:
        stukken.append((begin, eind + EINDE))


def nieuwe_tijd(t: float) -> float:
    """Tijdstip in de geknipte video."""
    verstreken = 0.0
    for a, b in stukken:
        if t <= b:
            return verstreken + max(0.0, t - a)
        verstreken += b - a
    return verstreken


filters = []
for j, (a, b) in enumerate(stukken):
    filters.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{j}]")
filters.append(
    "".join(f"[v{j}]" for j in range(len(stukken)))
    + f"concat=n={len(stukken)}:v=1:a=0[vc]"
)
## Balk onder het beeld met per stap de ondertitel.
teksten = []
TEKSTMAP = DEMO / "ondertitels"
TEKSTMAP.mkdir(exist_ok=True)
for naam, t, lees in stappen:
    pad = TEKSTMAP / f"{naam}.txt"
    ## Bytes: write_text maakt op Windows \r\n van een regeleinde, en ffmpeg
    ## tekent dat als een extra regel.
    tekst = "\n".join(textwrap.wrap(ONDERTITEL[naam], 90))
    pad.write_bytes(tekst.encode("utf-8"))
    van = nieuwe_tijd(t)
    tot = van + lees + 0.7
    tekstpad = pad.relative_to(DEMO.parent).as_posix()
    teksten.append(
        f"drawtext=fontfile='{LETTER}':textfile='{tekstpad}':fontsize=28:"
        "fontcolor=white:line_spacing=8:x=(w-text_w)/2:"
        f"expansion=none:y=h-{BALK}+({BALK}-text_h)/2:enable='between(t,{van:.2f},{tot:.2f})'"
    )
filters.append(f"[vc]pad=iw:ih+{BALK}:0:0:color=0x0f172a," + ",".join(teksten) + "[v]")
invoer = ["-i", str(TAKE)]

subprocess.run(
    cwd=DEMO.parent,
    args=[
        "ffmpeg",
        "-y",
        "-loglevel",
        "error",
        *invoer,
        "-filter_complex",
        ";".join(filters),
        "-map",
        "[v]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-an",
        "-movflags",
        "+faststart",
        str(UIT),
    ],
    check=True,
)
totaal = sum(b - a for a, b in stukken)
print(f"Klaar: {UIT} ({totaal:.0f} s, {UIT.stat().st_size / 1e6:.1f} MB)")
