"""Loopbanen: stapelen, opstromen, afstromen, studiewissel en uitval na de start."""

import altair as alt
import polars as pl
import streamlit as st

from staat_mbo import overzicht as ov
from staat_mbo.app import ui
from staat_mbo.cohorten import CATEGORIEEN
from staat_mbo.definities import CATEGORIE_KLEUREN, CATEGORIE_TOELICHTING, DEFINITIES

CATEGORIEKLEUR = alt.Scale(domain=CATEGORIEEN, range=CATEGORIE_KLEUREN)
## Welke categorieën bij een keuze horen; None is alles.
UITKOMSTEN = {
    "Alle categorieën": None,
    "Stapelen": [CATEGORIEEN[0]],
    "Opstromen": [CATEGORIEEN[5]],
    "Afstromen": [CATEGORIEEN[6]],
    "Studiewissel": [CATEGORIEEN[4]],
    "Uitval": [CATEGORIEEN[7]],
}
VERDELING = {"Per cohort en niveau": ["Cohort", "Niveau"], "Per cohort": ["Cohort"]}
WISSEL_UITLEG = (
    "Stapelen telt niet als wissel: wie na een diploma verder gaat op een hoger "
    "niveau staat bij 'Diploma, verder op hoger niveau'. Ook opstromen en "
    "afstromen zijn geen wissel; alleen een ander crebo op hetzelfde niveau "
    "zonder diploma is dat."
)


def staafgrafiek(v: pl.DataFrame, per: list[str], keuze: list[str] | None) -> None:
    """Percentage per cohort (en niveau) en categorie; vaste volgorde en kleuren."""
    data = v.with_columns(
        pl.col("Cohort").cast(pl.Utf8),
        pl.col("Status")
        .replace_strict(
            {c: i for i, c in enumerate(CATEGORIEEN)}, return_dtype=pl.Int32
        )
        .alias("Volgorde"),
    )
    if keuze:
        data = data.filter(pl.col("Status").is_in(keuze))
    if "Niveau" in per:
        data = data.with_columns(
            pl.format("Niveau {}", pl.col("Niveau")).alias("Niveau")
        )
    grafiek = (
        alt.Chart(data.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Cohort:O", title="Instroomcohort"),
            y=alt.Y(
                "Percentage:Q",
                title="% van het cohort",
                scale=alt.Scale(domain=[0, 100]),
            ),
            color=alt.Color(
                "Status:N",
                scale=CATEGORIEKLEUR,
                sort=CATEGORIEEN,
                legend=alt.Legend(orient="bottom", columns=2, title=None),
            ),
            order=alt.Order("Volgorde:Q"),
            tooltip=[
                "Cohort",
                "Status",
                "Aantal",
                alt.Tooltip("Percentage:Q", format=".1f"),
            ],
        )
    )
    if "Niveau" in per:
        grafiek = grafiek.encode(column=alt.Column("Niveau:N", title=None))
    st.altair_chart(grafiek, width="stretch")


def matrix(overgangen: pl.DataFrame) -> None:
    st.subheader("Van niveau naar niveau")
    st.caption(
        "Niveau op 1 oktober van het cohortjaar (rijen) naar het niveau een jaar later "
        "(kolommen); 'weg' is niet meer bij de instelling. Stapelen is een diploma "
        "en dan een hoger niveau, opstromen hetzelfde zonder diploma."
    )
    links, midden, rechts = st.columns(3)
    diploma = links.radio(
        "Diploma in dat jaartijdvak",
        ["Alle", "Met diploma", "Zonder diploma"],
        horizontal=True,
    )
    jaren = sorted(overgangen["Jaar"].unique())
    gekozen = midden.multiselect(
        "Jaar van de 1 oktober", jaren, placeholder="Alle jaren"
    )
    weergave = rechts.radio("Toon", ["Aantal", "% van de rij"], horizontal=True)
    df = overgangen.filter(pl.col("Jaar").is_in(gekozen)) if gekozen else overgangen
    tabel = ov.overgangsmatrix(
        df, {"Alle": None, "Met diploma": True}.get(diploma, False)
    )
    if weergave != "Aantal":
        kolommen = [c for c in tabel.columns if c != "Van"]
        totaal = pl.sum_horizontal(kolommen)
        tabel = tabel.with_columns(
            pl.when(totaal > 0).then(pl.col(c) / totaal * 100).round(1).alias(c)
            for c in kolommen
        )
    ui.toon_tabel(tabel, "niveau_overgangen")


st.title("Loopbanen")
analyse = ui.vereis_analyse()
resultaten = ui.resultaten(analyse)
filters = ui.filters(analyse)
ui.toon_label()

loopbanen = ui.filter_toepassen(resultaten.loopbanen, filters, analyse, True)
if loopbanen.is_empty():
    st.info("Geen loopbanen voor deze selectie.")
    ui.toon_dekkingsmeldingen(analyse)
    st.stop()
ui.toon_dekkingsmeldingen(analyse)

st.subheader("Loopbaanstatus na de start", help=DEFINITIES["loopbaanstatus"])
links, midden, rechts = st.columns(3)
jaren = links.radio(
    "Na",
    [1, 2, 3],
    format_func=lambda k: f"na {k} jaar",
    horizontal=True,
    help="Gemeten op 1 oktober, zoveel jaar na de start van het cohort.",
)
uitkomst = midden.selectbox("Toon", list(UITKOMSTEN))
per = VERDELING[rechts.radio("Verdeel", list(VERDELING), horizontal=True)]

if uitkomst == "Studiewissel":
    st.caption(WISSEL_UITLEG)
    st.caption(DEFINITIES["studiewissel"])

verdeling = ov.verdeling(loopbanen.filter(pl.col("Jaren") == jaren), per)
staafgrafiek(verdeling, per, UITKOMSTEN[uitkomst])

st.markdown("**Verdeling in procenten** (elke rij telt op tot 100%)")
ui.toon_tabel(
    ov.verdeling_tabel(loopbanen.filter(pl.col("Jaren") == jaren), per),
    f"loopbaanstatus_na_{jaren}_jaar",
)

with st.expander("Wat betekenen de categorieën?"):
    for categorie in CATEGORIEEN:
        st.markdown(f"**{categorie}**: {CATEGORIE_TOELICHTING[categorie]}")

matrix(ui.filter_toepassen(resultaten.overgangen, filters, analyse))
