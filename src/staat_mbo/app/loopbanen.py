"""Pagina Loopbanen (volgt)."""

import streamlit as st

from staat_mbo.app import ui

st.title("Loopbanen")
ui.vereis_analyse()
ui.toon_label()
