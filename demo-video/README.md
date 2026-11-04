# Demovideo opnieuw maken

Doe dit als het dashboard zichtbaar verandert. De opname kiest de RO-bestanden uit `src/staat_mbo/demodata/` echt via de bestandskiezer (dus niet de knop "Probeer met demodata"), klikt op Samenvoegen en loopt dan Start, Studiesucces, Cohorten, Loopbanen en Over de cijfers langs (24 stappen). Bij elk uitgelegd element staan een kader, een pijl en een chip; de ondertitels staan in een balk onder het beeld. De video heeft geen geluid; elke stap blijft zo lang in beeld als nodig is om de ondertitel te lezen (`leestijd` in `stappen.py`).

Voor de opname is de pagina smaller gemaakt (CSS in `record.py`), zodat de chip in de rechtermarge past; kan dat niet, dan komt hij in een lege band onder het blok. De getallen in `stappen.py` (`WAARDEN`, `STUDIESUCCES`) worden tegen de pagina gecontroleerd: staat er iets anders, dan stopt de opname.

```
uv sync --group demo
uv run --group demo python -m playwright install chromium
uv run smbo dashboard --poort 8599 --geen-browser           # in een tweede terminal, zonder --invoer
uv run --group demo python demo-video/scenes/record.py      # opname (poort via STAAT_MBO_POORT)
uv run python demo-video/stitch.py                          # knippen, ondertitels erbij, wachttijd eruit
```

Het resultaat is `demo-video/demo_final.mp4` (niet in git). `ffmpeg` moet in je pad staan. Raakt een kader, chip of pijl een ander element, dan stopt de opname met een fout; pas dan het element of de ruimte aan in `scenes/record.py`. Met `STAAT_MBO_SHOTS=<map> STAAT_MBO_DROOG=1` maak je snel een screenshot per stap om te controleren.

Zet de video in de README via github.com: bewerk `README.md`, sleep `demo_final.mp4` op de plek van de TODO-opmerking bovenaan en sla op. GitHub maakt er een link van die in de README afspeelt. De video zelf komt niet in git.

Tekst aanpassen: `stappen.py` (ondertitel van hooguit 110 tekens en chip per stap), daarna alle stappen opnieuw.
