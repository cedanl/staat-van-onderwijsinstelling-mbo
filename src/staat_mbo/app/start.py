"""Start: bestanden kiezen, samenvoegen en de meldingen lezen."""

import streamlit as st

from staat_mbo.analyse import DEMODATA, kerncijfers
from staat_mbo.app import invoer, ui

st.title("Staat van de Onderwijsinstelling MBO")
st.write(
    "Kies al je RO- en TBG-i-bestanden tegelijk, of de uitvoer van "
    "mbo-bekostiging-bestanden (datamodel of zip). Klik dan op **Samenvoegen**."
)
st.caption(
    "Persoonsnummers worden vervangen door een code; behandel alles als "
    "persoonsgegevens. De bestanden blijven op deze computer."
)

gekozen = st.file_uploader(
    "Kies je bestanden",
    accept_multiple_files=True,
    help="RO en TBG-i van DUO, of een datamodel/zip van mbo-bekostiging-bestanden. "
    "De bestanden gaan alleen naar een tijdelijke werkmap op deze computer.",
)
links, rechts, _ = st.columns([1, 1, 2])
samenvoegen = links.button("Samenvoegen", type="primary", width="stretch")
demo = rechts.button(
    "Probeer met demodata",
    width="stretch",
    help="Verzonnen RO's van één instelling, zonder echte studenten.",
)

if demo:
    ui.laad_map(DEMODATA)
elif samenvoegen:
    if not gekozen:
        st.warning("Kies eerst je bestanden.")
    else:
        selectie = invoer.synchroniseer_selectie(
            ((f.name, f.getvalue()) for f in gekozen), ui.werkmap()
        )
        ui.laad_invoer([selectie])

analyse = ui.huidige_analyse()
if analyse is not None:
    ui.toon_meldingen(analyse)
    if analyse.ok:
        st.subheader("In je bestanden")
        st.caption(
            "Tellingen, zonder definitiekeuzes. Studiesucces, cohorten en "
            "loopbanen staan op de andere pagina's, met hun definitie erbij."
        )
        tegels = kerncijfers(analyse)
        for rij in (tegels[:3], tegels[3:]):
            for kolom, t in zip(st.columns(3), rij, strict=True):
                kolom.metric(t.naam, t.waarde, help=t.help or None)
                kolom.caption(t.ondertitel)
        st.caption(
            "Kies links een pagina: Studiesucces, Cohorten, Loopbanen of "
            "Over de cijfers."
        )
