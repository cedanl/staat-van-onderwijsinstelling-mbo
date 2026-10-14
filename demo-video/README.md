# Demovideo opnieuw maken

Doe dit als het dashboard zichtbaar verandert. Alles draait op de demodata in `tests/fixtures/ruw`.

```
uv sync --group demo
uv run --group demo python -m playwright install chromium
uv run --group demo python demo-video/generate_audio.py     # voice-over per stap (piper)
MBO_PSEUDONIMISERING_SALT=demo STAAT_MBO_POORT=8791 uv run smbo dashboard   # in een tweede terminal
uv run --group demo python demo-video/scenes/record.py      # opname
uv run python demo-video/stitch.py                          # video + stem, wachttijd eruit
gh release upload demo-videos demo-video/demo_final.mp4 --clobber
```

Tekst aanpassen: `stappen.py` (ondertitel en uitspraak per stap), daarna alle stappen opnieuw.
