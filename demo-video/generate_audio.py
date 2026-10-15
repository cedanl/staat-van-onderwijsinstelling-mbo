"""Voice-over per stap met piper-tts (hoogste Nederlandse kwaliteit).

Schrijft audio/<stap>.wav, audio/duren.json en narration.txt.
Aanroep: uv run --group demo python demo-video/generate_audio.py
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

from piper import PiperVoice

sys.path.insert(0, str(Path(__file__).parent))
from stappen import STAPPEN

DEMO = Path(__file__).parent
VOICES = DEMO / "voices"
AUDIO = DEMO / "audio"
VOICE = "nl_NL-mls-medium"

VOICES.mkdir(exist_ok=True)
AUDIO.mkdir(exist_ok=True)
if not (VOICES / f"{VOICE}.onnx").exists():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "piper.download_voices",
            "--download-dir",
            str(VOICES),
            VOICE,
        ],
        check=True,
    )
voice = PiperVoice.load(str(VOICES / f"{VOICE}.onnx"))

duren = {}
for naam, _, uitspraak in STAPPEN:
    pad = AUDIO / f"{naam}.wav"
    with wave.open(str(pad), "wb") as wav:
        voice.synthesize_wav(uitspraak, wav)
    with wave.open(str(pad), "rb") as f:
        duren[naam] = f.getnframes() / f.getframerate()
    print(f"{naam}: {duren[naam]:.1f}s")

(AUDIO / "duren.json").write_text(json.dumps(duren, indent=2))
(DEMO / "narration.txt").write_text(
    "\n".join(u for _, _, u in STAPPEN) + "\n", encoding="utf-8"
)
print(f"Totaal: {sum(duren.values()):.1f}s")
