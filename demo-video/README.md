# Demovideo opnieuw maken

Doe dit als het dashboard zichtbaar verandert. Alles draait op de demodata in `demodata/`.

```
uv sync --group demo
uv run --group demo python -m playwright install chromium
uv run --group demo python demo-video/generate_audio.py     # voice-over per stap (piper)
STAAT_MBO_POORT=8791 uv run smbo dashboard   # in een tweede terminal
uv run --group demo python demo-video/scenes/record.py      # opname
uv run python demo-video/stitch.py                          # video + stem, wachttijd eruit
```

Zet de video in de README via github.com: bewerk `README.md`, sleep `demo_final.mp4` op de plek van de video en sla op. GitHub maakt er een link van die in de README afspeelt. De video zelf komt niet in git.

Tekst aanpassen: `stappen.py` (ondertitel en uitspraak per stap), daarna alle stappen opnieuw.
