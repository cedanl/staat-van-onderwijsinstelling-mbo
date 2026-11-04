"""Npuls-huisstijl voor het dashboard: CSS, logo en één thema voor alle grafieken.

Bron: vormgever-npuls-huisstijl (design-tokens.json). Het Streamlit-thema zelf
staat in ``staat_mbo.palet.THEMA`` en gaat via ``smbo dashboard`` als
``--theme.*`` mee; hier komt de rest: lettertype, koppen, kaarten en meldingen.
"""

from pathlib import Path

import altair as alt

## Altair kijkt in sys.modules of pandas er al is. Importeert een andere
## sessie pandas op dat moment nog, dan ziet Altair een half geladen module
## (AttributeError: partially initialized module 'pandas'). Een gewone import
## vooraf wacht op de importlock en voorkomt dat.
import pandas  # noqa: F401
import streamlit as st

from staat_mbo import palet

_MAP = Path(__file__).parent
CSS = _MAP / "huisstijl.css"
LOGO = _MAP / "assets" / "npuls_logo.jpg"
_RAND = {"left": 14, "right": 14, "top": 14, "bottom": 14}


def css() -> str:
    """De stijlblokken van de huisstijl, klaar om in de pagina te zetten."""
    return f"<style>{CSS.read_text(encoding='utf-8')}</style>"


def toepassen() -> None:
    """Zet CSS en logo op de pagina; aanroepen vóór de pagina's draaien."""
    st.markdown(css(), unsafe_allow_html=True)
    st.logo(str(LOGO), size="large")


def schaal(domein: list[str], kleuren: list[str]) -> alt.Scale:
    """Vaste kleur per categorie, in de volgorde van het domein."""
    return alt.Scale(domain=domein, range=kleuren)


def stijl(grafiek: alt.TopLevelMixin) -> alt.TopLevelMixin:
    """Het gedeelde grafiekthema: wit vlak, lettertype, grijze rasterlijnen."""
    return (
        grafiek.properties(padding=_RAND)
        .configure(background=palet.WIT, font=palet.FONT)
        .configure_view(stroke=None)
        .configure_axis(
            gridColor=palet.GRIJS_200,
            domainColor=palet.GRIJS_400,
            tickColor=palet.GRIJS_400,
            labelColor=palet.ZWART,
            titleColor=palet.ZWART,
            labelFont=palet.FONT,
            titleFont=palet.FONT,
            titleFontWeight=600,
            titlePadding=12,
            labelPadding=4,
        )
        .configure_legend(
            labelColor=palet.ZWART,
            titleColor=palet.ZWART,
            labelFont=palet.FONT,
            titleFont=palet.FONT,
            symbolType="square",
            labelLimit=400,
        )
        .configure_header(
            labelColor=palet.ZWART, titleColor=palet.ZWART, labelFont=palet.FONT
        )
    )


def toon_grafiek(grafiek: alt.TopLevelMixin) -> None:
    """Teken een Altair-grafiek in de huisstijl."""
    st.altair_chart(stijl(grafiek), width="stretch", theme=None)
