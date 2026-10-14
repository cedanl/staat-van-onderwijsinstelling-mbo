"""Video + voice-over samenvoegen tot demo_final.mp4.

Elke audioclip start op het moment dat zijn stap in beeld komt
(scenes/tijden.json). Wachttijd tussen stappen (rekenen, laden) wordt
weggeknipt tot een korte overgang.
Aanroep: uv run python demo-video/stitch.py
"""

import json
import subprocess
import wave
from pathlib import Path

DEMO = Path(__file__).parent
TAKE = DEMO / "scenes" / "take.webm"
UIT = DEMO / "demo_final.mp4"
NA_STAP = 2.2  # seconden na de voice-over die in beeld blijven (klik, begin van laden)
VOOR_STAP = 1.0  # seconden vóór de volgende stap
EINDE = 2.0


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
    + f"concat=n={len(stukken)}:v=1:a=0[v]"
)
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
    ["ffmpeg", "-y", "-loglevel", "error", *invoer,
     "-filter_complex", ";".join(filters),
     "-map", "[v]", "-map", "[a]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-pix_fmt", "yuv420p",
     "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(UIT)],
    check=True,
)
totaal = sum(b - a for a, b in stukken)
print(f"Klaar: {UIT} ({totaal:.0f} s, {UIT.stat().st_size / 1e6:.1f} MB)")
