"""Studiesucces: jaar-, diploma- en startersresultaat als driejaarscijfer."""

import altair as alt
import polars as pl
import streamlit as st

from staat_mbo import overzicht as ov
from staat_mbo.app import ui
from staat_mbo.definities import DEFINITIES, NORM_LABEL

NAMEN = {"JR": "Jaarresultaat", "DR": "Diplomaresultaat", "SR": "Startersresultaat"}
GROEPERINGEN = {
    "Opleiding en leerweg": ["Opleidingcode", "Niveau", "Leertraject"],
    "Opleiding": ["Opleidingcode", "Niveau"],
    "Niveau": ["Niveau"],
}
## Neutrale kleuren per niveau (geen rood of groen).
NIVEAUKLEUR = alt.Scale(
    domain=["Niveau 1", "Niveau 2", "Niveau 3", "Niveau 4"],
    range=["#9aa5b1", "#4c78a8", "#f58518", "#b279a2"],
)


def tegel(kolom, indicator: str, rij: dict | None) -> None:
    hulp = DEFINITIES[indicator.lower()]
    if rij is None:
        kolom.metric(NAMEN[indicator], "nog geen driejaarscijfer", help=hulp)
        return
    kolom.metric(NAMEN[indicator], ov.cel(rij), help=hulp)
    regels = [f"{rij['Periode']} · n = {rij['Noemer']}"]
    if rij["Norm"] is not None:
        regels.append(f"{NORM_LABEL}: {rij['Norm']}%")
    if not rij["Volledig"]:
        regels.append(f"{ov.ONVOLLEDIG} onvolledig: zie Over de cijfers")
    kolom.caption("  \n".join(regels))


def tijdlijn(df: pl.DataFrame, indicator: str) -> None:
    d = (
        df.filter(
            (pl.col("Indicator") == indicator) & pl.col("Percentage").is_not_null()
        )
        .with_columns(
            pl.format("Niveau {}", pl.col("Niveau")).alias("Niveau"),
            pl.format("{}-{}", pl.col("Jaartijdvak"), pl.col("Jaartijdvak") + 1).alias(
                "Tot"
            ),
        )
        .select("Tot", "Periode", "Niveau", "Percentage", "Norm", "Teller", "Noemer")
    )
    if d.is_empty():
        st.caption(f"{NAMEN[indicator]}: nog geen driejaarscijfer te tekenen.")
        return
    x = alt.X("Tot:O", title="Driejaarscijfer t/m jaartijdvak")
    kleur = alt.Color("Niveau:N", scale=NIVEAUKLEUR, legend=alt.Legend(orient="bottom"))
    lijn = (
        alt.Chart(d.to_pandas())
        .mark_line(point=True)
        .encode(
            x=x,
            y=alt.Y("Percentage:Q", title="%", scale=alt.Scale(domain=[0, 100])),
            color=kleur,
            tooltip=["Periode", "Niveau", "Percentage", "Teller", "Noemer"],
        )
    )
    norm = (
        alt.Chart(d.drop_nulls("Norm").to_pandas())
        .mark_line(strokeDash=[4, 4], opacity=0.7)
        .encode(x=x, y=alt.Y("Norm:Q"), color=kleur, tooltip=["Niveau", "Norm"])
    )
    st.subheader(NAMEN[indicator])
    st.altair_chart(lijn + norm, width="stretch")


st.title("Studiesucces")
analyse = ui.vereis_analyse()
resultaten = ui.resultaten(analyse)
filters = ui.filters(analyse)
ui.toon_label()

basis = ui.filter_toepassen(
    resultaten.studiesucces.filter(pl.col("Groep") == "opleiding_leerweg"),
    filters,
    analyse,
)
if basis.is_empty():
    st.info(
        "Geen driejaarscijfers voor deze selectie. Zie de meldingen hieronder "
        "voor wat je bestanden nodig hebben."
    )
    ui.toon_dekkingsmeldingen(analyse)
    st.stop()

tegels = {
    r["Indicator"]: r for r in ov.aggregeer(ov.laatste(basis), []).iter_rows(named=True)
}
for kolom, indicator in zip(st.columns(3), ov.INDICATOREN, strict=True):
    tegel(kolom, indicator, tegels.get(indicator))
ui.toon_dekkingsmeldingen(analyse)

st.subheader("Per opleiding")
keuze = st.radio(
    "Toon per",
    list(GROEPERINGEN),
    horizontal=True,
    help="Tel de opleidingen op tot opleiding of niveau.",
)
sleutel = GROEPERINGEN[keuze]
tabel = ov.tabel_studiesucces(ov.aggregeer(ov.laatste(basis), sleutel), sleutel)
if "Opleidingcode" in sleutel:
    tabel = ov.met_opleiding(tabel, analyse.opleidingen).drop("Opleidingcode")
tabel = tabel.rename({"Leertraject": "Leerweg"}, strict=False)
volgorde = [c for c in ("Opleiding", "Niveau", "Leerweg") if c in tabel.columns]
tabel = tabel.sort(volgorde).select(*volgorde, "JR", "DR", "SR", "n", "Norm")
perioden = dict(ov.laatste(basis).select("Indicator", "Periode").unique().iter_rows())
st.caption(
    "Laatste driejaarscijfer: "
    + "; ".join(f"{NAMEN[i]} {perioden[i]}" for i in ov.INDICATOREN if i in perioden)
    + f". {ov.ONVOLLEDIG} = onvolledig (ondergrens of verkorte terugblik, "
    "zie Over de cijfers). n = noemer van JR / DR / SR; "
    f"Norm = {NORM_LABEL} (JR / DR / SR) voor het niveau."
)
ui.toon_tabel(tabel, "studiesucces")

st.subheader("Verloop per niveau")
verloop = ov.aggregeer(basis, ["Niveau"])
kolommen = st.columns(3)
for kolom, indicator in zip(kolommen, ov.INDICATOREN, strict=True):
    with kolom:
        tijdlijn(verloop, indicator)
st.caption(f"Stippellijn: {NORM_LABEL}, per niveau.")
