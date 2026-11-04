"""Ingang van de Streamlit-app: pagina's en navigatie."""

from pathlib import Path

import streamlit as st

_MAP = Path(__file__).parent

st.set_page_config(page_title="Staat van de Onderwijsinstelling MBO", layout="wide")

pagina = st.navigation(
    [
        st.Page(_MAP / "start.py", title="Start", default=True),
        st.Page(_MAP / "studiesucces.py", title="Studiesucces"),
        st.Page(_MAP / "cohorten.py", title="Cohorten"),
        st.Page(_MAP / "loopbanen.py", title="Loopbanen"),
        st.Page(_MAP / "over.py", title="Over de cijfers"),
    ],
    position="sidebar",
)
pagina.run()
