"""Gedeelde bouwstenen van de pagina's: sessie, filters, tabellen en meldingen."""

import os
import tempfile
from pathlib import Path

import polars as pl
import streamlit as st
from mbo_bekostiging_bestanden.waardenlijsten import (
    leertrajecten_buiten_indicatorpopulatie,
)

from staat_mbo.analyse import Analyse, Resultaten, bereken, maak_analyse
from staat_mbo.app.invoer import maak_werkmap
from staat_mbo.definities import LABEL
from staat_mbo.overzicht import Filters, met_opleiding, toepassen

SESSIE_ANALYSE = "analyse"
SESSIE_WERKMAP = "selectie_werkmap"
## Map met bestanden die de app bij de start laadt (opnames en tests).
OMGEVING_INVOER = "STAAT_MBO_INVOER"
_WAARSCHUWING = "Let op: "
_INFO = "Info: "
_ADVIES = "Voeg eerst je bestanden samen op de pagina Start."


def werkmap() -> Path:
    """Werkmap van deze sessie voor de gekozen bestanden."""
    return Path(st.session_state.setdefault(SESSIE_WERKMAP, str(maak_werkmap())))


def _analyseer(invoer: list[Path]) -> Analyse:
    with tempfile.TemporaryDirectory(
        prefix="smbo-werk-", ignore_cleanup_errors=True
    ) as tijdelijk:
        return maak_analyse(invoer, Path(tijdelijk))


@st.cache_resource(show_spinner="Bestanden samenvoegen…")
def _analyse_van_map(pad: str) -> Analyse:
    return _analyseer([Path(pad)])


def laad_invoer(invoer: list[Path]) -> Analyse:
    """Voeg de invoer samen en bewaar het resultaat in de sessie."""
    with st.spinner("Bestanden samenvoegen…"):
        analyse = _analyseer(invoer)
    st.session_state[SESSIE_ANALYSE] = analyse
    return analyse


def laad_map(pad: Path) -> Analyse:
    """Als [laad_invoer] voor één map, onthouden tussen sessies (demodata)."""
    analyse = _analyse_van_map(str(pad))
    st.session_state[SESSIE_ANALYSE] = analyse
    return analyse


def huidige_analyse() -> Analyse | None:
    """De analyse van deze sessie; bij de start uit ``STAAT_MBO_INVOER`` indien gezet."""
    if SESSIE_ANALYSE not in st.session_state and (
        pad := os.environ.get(OMGEVING_INVOER)
    ):
        laad_map(Path(pad))
    return st.session_state.get(SESSIE_ANALYSE)


def toon_meldingen(analyse: Analyse) -> None:
    """Gelukt of niet gelukt, met de meldingen van stapelcontrole en historie."""
    regels = analyse.regels()
    if not analyse.ok:
        st.error("  \n".join([f"**{regels[0]}**", *regels[1:]]))
        return
    st.success(regels[0])
    kaal = [r for r in regels[1:] if not r.startswith((_WAARSCHUWING, _INFO))]
    st.markdown("\n".join(f"- {r}" for r in kaal))
    for r in regels[1:]:
        if r.startswith(_WAARSCHUWING):
            st.warning(r.removeprefix(_WAARSCHUWING))
        elif r.startswith(_INFO):
            st.info(r.removeprefix(_INFO))


def vereis_analyse() -> Analyse:
    """De analyse, of een uitleg en stop als er (nog) geen goede is."""
    analyse = huidige_analyse()
    if analyse is not None and not analyse.ok:
        toon_meldingen(analyse)
    if analyse is None or not analyse.ok:
        st.info(_ADVIES)
        st.stop()
    return analyse


@st.cache_data(show_spinner="Cijfers berekenen…")
def _resultaten(_analyse: Analyse, sleutel: str) -> Resultaten:
    return bereken(_analyse)


def resultaten(analyse: Analyse) -> Resultaten:
    """De berekende tabellen, onthouden zolang de invoer niet verandert."""
    return _resultaten(analyse, analyse.sleutel)


def toon_label() -> None:
    """De vaste melding dat de cijfers indicatief zijn (ontwerp §3)."""
    st.info(LABEL)


def filters(analyse: Analyse) -> Filters:
    """Filters in de zijbalk; ze gelden op alle pagina's."""
    populatie = analyse.peilmomenten.filter(
        pl.col("Niveau").is_not_null()
        & ~pl.col("Leertraject").is_in(leertrajecten_buiten_indicatorpopulatie())
    )
    codes = populatie["Opleidingcode"].unique().to_list()
    in_populatie = analyse.opleidingen.filter(pl.col("Opleidingcode").is_in(codes))
    label = dict(
        met_opleiding(in_populatie, analyse.opleidingen)
        .select("Opleidingcode", "Opleiding")
        .sort("Opleiding")
        .iter_rows()
    )
    domeinen = sorted(in_populatie["Opleiding_domein"].drop_nulls().unique())
    with st.sidebar:
        st.header("Filters")
        st.caption("Gelden op alle pagina's.")
        niveaus = st.multiselect(
            "Niveau",
            sorted(populatie["Niveau"].unique()),
            format_func=lambda n: f"Niveau {n}",
            placeholder="Alle niveaus",
            key="filter_niveau",
        )
        leerwegen = st.multiselect(
            "Leerweg",
            sorted(populatie["Leertraject"].unique()),
            placeholder="Alle leerwegen",
            key="filter_leerweg",
        )
        domein = st.multiselect(
            "Domein", domeinen, placeholder="Alle domeinen", key="filter_domein"
        )
        gekozen = st.multiselect(
            "Opleiding",
            list(label),
            format_func=lambda c: label.get(c, c),
            placeholder="Alle opleidingen",
            key="filter_opleiding",
        )
    return Filters(tuple(niveaus), tuple(leerwegen), tuple(domein), tuple(gekozen))


def filter_toepassen(df: pl.DataFrame, f: Filters, analyse: Analyse) -> pl.DataFrame:
    """Pas de filters uit de zijbalk toe op een tabel met crebo, niveau en leerweg."""
    return toepassen(df, f, analyse.opleidingen)


def toon_tabel(df: pl.DataFrame, bestandsnaam: str, **kolommen) -> None:
    """Tabel zonder index, met een download van wat er staat (alleen geaggregeerd)."""
    st.dataframe(df, hide_index=True, width="stretch", column_config=kolommen or None)
    st.download_button(
        f"Download {bestandsnaam}.csv",
        df.write_csv(),
        file_name=f"{bestandsnaam}.csv",
        mime="text/csv",
        key=f"download_{bestandsnaam}",
    )


def toon_dekkingsmeldingen(analyse: Analyse) -> None:
    """De meldingen over de dekking van de bestanden, ingeklapt onder de cijfers."""
    meldingen = [*analyse.rapport.waarschuwingen, *(m.tekst for m in analyse.meldingen)]
    if meldingen:
        with st.expander(f"Meldingen over je bestanden ({len(meldingen)})"):
            for tekst in meldingen:
                st.markdown(f"- {tekst}")
