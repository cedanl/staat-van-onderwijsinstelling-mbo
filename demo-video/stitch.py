"""Video + voice-over samenvoegen tot demo_final.mp4.

Elke audioclip start op het moment dat zijn stap in beeld komt
(scenes/tijden.json). Wachttijd tussen stappen (rekenen, laden) wordt
weggeknipt tot een korte overgang. De ondertitels staan in een balk onder het
beeld van de app, zodat ze nooit iets in de app afdekken.
Aanroep: uv run python demo-video/stitch.py
"""

import json
import subprocess
import sys
import textwrap
import wave
from pathlib import Path

DEMO = Path(__file__).parent
sys.path.insert(0, str(DEMO))
from stappen import STAPPEN

TAKE = DEMO / "scenes" / "take.webm"
UIT = DEMO / "demo_final.mp4"
NA_STAP = 2.2  # seconden na de voice-over die in beeld blijven (klik, begin van laden)
VOOR_STAP = 1.0  # seconden vóór de volgende stap
EINDE = 2.0
BALK = 120  # hoogte van de ondertitelbalk onder het beeld
LETTER = r"C\:/Windows/Fonts/segoeuib.ttf"
ONDERTITEL = {naam: sub for naam, sub, _ in STAPPEN}


def duur(pad: Path) -> float:
    with wave.open(str(pad), "rb") as f:
        return f.getnframes() / f.getframerate()


tijden = json.loads((DEMO / "scenes" / "tijden.json").read_text())["tijden"]
start = max(0.0, tijden.pop("_klaar") - 0.3)
stappen = [(naam, t, DEMO / "audio" / f"{naam}.wav") for naam, t in tijden.items()]

## Te bewaren stukken van de opname.
stukken = []
begin = start
for i, (_, t, wav) in enumerate(stappen):
    eind = t + duur(wav) + NA_STAP
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
for naam, t, wav in stappen:
    pad = DEMO / "audio" / f"ondertitel_{naam}.txt"
    pad.write_text("\n".join(textwrap.wrap(ONDERTITEL[naam], 68)), encoding="utf-8")
    van = nieuwe_tijd(t)
    tot = van + duur(wav) + 0.7
    tekstpad = pad.relative_to(DEMO.parent).as_posix()
    teksten.append(
        f"drawtext=fontfile='{LETTER}':textfile='{tekstpad}':fontsize=28:"
        "fontcolor=white:line_spacing=8:x=(w-text_w)/2:"
        f"y=h-{BALK}+({BALK}-text_h)/2:enable='between(t,{van:.2f},{tot:.2f})'"
    )
filters.append(f"[vc]pad=iw:ih+{BALK}:0:0:color=0x0f172a," + ",".join(teksten) + "[v]")
invoer = ["-i", str(TAKE)]
for i, (_, t, wav) in enumerate(stappen, start=1):
    invoer += ["-i", str(wav)]
    ms = int(nieuwe_tijd(t) * 1000)
    filters.append(f"[{i}:a]adelay={ms}|{ms}[a{i}]")
filters.append(
    "".join(f"[a{i}]" for i in range(1, len(stappen) + 1))
    + f"amix=inputs={len(stappen)}:normalize=0[a]"
)

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
        "-map",
        "[a]",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "24",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(UIT),
    ],
    check=True,
)
totaal = sum(b - a for a, b in stukken)
print(f"Klaar: {UIT} ({totaal:.0f} s, {UIT.stat().st_size / 1e6:.1f} MB)")
