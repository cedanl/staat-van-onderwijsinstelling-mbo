# Demovideo opnieuw maken

Doe dit als het dashboard zichtbaar verandert. De opname klikt in de app op **Probeer met demodata** (`src/staat_mbo/demodata/`) en loopt dan de pagina's langs: Start, Studiesucces, Cohorten, Loopbanen en Over de cijfers. De voice-over is Nederlands (piper); de ondertitels staan in een balk onder het beeld en in de app staat alleen een kader om het uitgelegde element, dus er overlapt nooit iets.

```
uv sync --group demo
uv run --group demo python -m playwright install chromium
uv run --group demo python demo-video/generate_audio.py     # voice-over per stap (piper)
uv run smbo dashboard --poort 8599 --geen-browser           # in een tweede terminal
uv run --group demo python demo-video/scenes/record.py      # opname (poort via STAAT_MBO_POORT)
uv run python demo-video/stitch.py                          # video + stem, wachttijd eruit
```

Het resultaat is `demo-video/demo_final.mp4` (niet in git). `ffmpeg` moet in je pad staan. Raakt een kader een ander element, dan stopt de opname met een fout; pas dan het element of de ruimte van het kader aan in `scenes/record.py`.

Zet de video in de README via github.com: bewerk `README.md`, sleep `demo_final.mp4` op de plek van de TODO-opmerking bovenaan en sla op. GitHub maakt er een link van die in de README afspeelt. De video zelf komt niet in git.

Tekst aanpassen: `stappen.py` (ondertitel van hooguit 110 tekens en uitspraak per stap), daarna alle stappen opnieuw.
