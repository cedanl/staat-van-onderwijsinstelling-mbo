"""Over de cijfers: definities, bronnen, verschillen met de Inspectie en dekking."""

import polars as pl
import streamlit as st
from mbo_bekostiging_bestanden.indicatoren import norm_voor

from staat_mbo.analyse import dekking
from staat_mbo.app import ui
from staat_mbo.cohorten import CATEGORIEEN
from staat_mbo.definities import (
    BRONNEN,
    CATEGORIE_TOELICHTING,
    DEFINITIES,
    NAMEN,
    NORM_LABEL,
    VERSCHILLEN,
)
from staat_mbo.indicatoren import NIVEAUS

st.title("Over de cijfers")
analyse = ui.vereis_analyse()
ui.toon_label()

st.subheader("Wat betekenen de cijfers?")
for sleutel, tekst in DEFINITIES.items():
    st.markdown(f"**{NAMEN[sleutel]}.** {tekst}")
with st.expander("De negen loopbaanstatussen"):
    for categorie in CATEGORIEEN:
        st.markdown(f"**{categorie}**: {CATEGORIE_TOELICHTING[categorie]}")

st.subheader(NORM_LABEL[0].upper() + NORM_LABEL[1:])
st.caption(
    "De norm voor een voldoende driejaarscijfer per niveau, als referentielijn. "
    "Er hangt geen oordeel aan."
)
normen = pl.DataFrame(
    [
        {
            "Niveau": n,
            **{
                i.upper(): f"{norm_voor(i, n, 'voldoende')}%"
                for i in ("jr", "dr", "sr")
            },
        }
        for n in NIVEAUS
    ]
)
st.dataframe(normen, hide_index=True)

st.subheader("Waarin verschillen ze van de Inspectie?")
st.markdown("\n".join(f"- {tekst}" for tekst in VERSCHILLEN))

st.subheader("Bronnen")
st.markdown("\n".join(f"- [{naam}]({link})" for naam, link in BRONNEN.items()))

st.subheader("Wat dekken je bestanden?")
st.caption(
    "Per jaartijdvak (1 oktober t/m 30 september): ja = het cijfer is te berekenen "
    "en volledig; onvolledig = te berekenen, maar een ondergrens (diploma's van "
    "vóór je eerste RO ontbreken) of met een kortere terugblik dan zes jaar; "
    "nee = niet te berekenen. Een driejaarscijfer heeft drie opeenvolgende jaren "
    "met ja of onvolledig nodig."
)
st.dataframe(dekking(analyse.waarneming), hide_index=True, width="stretch")

st.subheader("Meldingen over je bestanden")
meldingen = [*analyse.rapport.waarschuwingen, *(m.tekst for m in analyse.meldingen)]
if meldingen:
    st.markdown("\n".join(f"- {tekst}" for tekst in meldingen))
else:
    st.write("Geen meldingen.")
