"""Cohorten: instroom, rendement nominaal en nominaal + 1, en uitval."""

import altair as alt
import polars as pl
import streamlit as st

from staat_mbo import overzicht as ov
from staat_mbo import palet
from staat_mbo.app import huisstijl, ui
from staat_mbo.cohorten import HERKOMSTEN
from staat_mbo.definities import DEFINITIES

HERKOMSTKLEUR = huisstijl.schaal(HERKOMSTEN, palet.HERKOMSTKLEUREN)
## Per maatstaf: titel, kolom en kleur; "nog niet waarneembaar" is grijs.
RENDEMENT = {
    "Nominaal": ("Nominaal_percentage", palet.BLAUW),
    "Nominaal + 1": ("Nominaal_plus_1_percentage", palet.ORANJE),
}
UITVAL = {
    "Uitval na 1 jaar": ("Uitval_1_percentage", palet.BLAUW),
    "Uitval na nominale duur": ("Uitval_duur_percentage", palet.ORANJE),
}
GRIJS = palet.NEUTRAAL


def instroomgrafiek(instroom: pl.DataFrame) -> None:
    data = ov.instroom_per_cohort(instroom).with_columns(pl.col("Cohort").cast(pl.Utf8))
    grafiek = (
        alt.Chart(data.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Cohort:O", title="Instroomcohort"),
            y=alt.Y("Aantal:Q", title="Studenten"),
            color=alt.Color(
                "Herkomst:N", scale=HERKOMSTKLEUR, legend=alt.Legend(orient="bottom")
            ),
            order=alt.Order("Herkomst:N"),
            tooltip=["Cohort", "Herkomst", "Aantal"],
        )
    )
    huisstijl.toon_grafiek(grafiek)


def _maatstaven(df: pl.DataFrame, maten: dict, grijs: bool) -> pl.DataFrame:
    """Lange tabel Cohort × maatstaf; een ontbrekend percentage wordt een grijze balk."""
    delen = []
    for naam, (kolom, _) in maten.items():
        delen.append(
            df.select(
                pl.col("Cohort").cast(pl.Utf8),
                pl.lit(naam).alias("Maatstaf"),
                pl.col(kolom).alias("Percentage"),
            )
        )
    lang = pl.concat(delen)
    soort = (
        pl.when(pl.col("Percentage").is_null())
        .then(pl.lit(ov.NOG_NIET))
        .otherwise(pl.col("Maatstaf"))
    )
    lang = lang.with_columns(soort.alias("Soort"))
    if grijs:
        return lang.with_columns(pl.col("Percentage").fill_null(100.0))
    return lang.drop_nulls("Percentage")


def percentagegrafiek(df: pl.DataFrame, maten: dict, titel: str) -> None:
    """Staven per cohort en maatstaf; niet-waarneembare cohorten zijn grijs."""
    data = _maatstaven(df, maten, grijs=True)
    kleur = huisstijl.schaal(
        [*maten, ov.NOG_NIET], [*(k for _, k in maten.values()), GRIJS]
    )
    grafiek = (
        alt.Chart(data.to_pandas())
        .mark_bar()
        .encode(
            x=alt.X("Cohort:O", title="Instroomcohort"),
            xOffset="Maatstaf:N",
            y=alt.Y("Percentage:Q", title=titel, scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "Soort:N", scale=kleur, legend=alt.Legend(orient="bottom", title=None)
            ),
            tooltip=["Cohort", "Maatstaf", "Soort", "Percentage"],
        )
    )
    huisstijl.toon_grafiek(grafiek)


def tekst(kolom: str) -> pl.Expr:
    """Percentage met komma, of "nog niet waarneembaar" bij een lege waarde."""
    return (
        pl.when(pl.col(kolom).is_null())
        .then(pl.lit(ov.NOG_NIET))
        .otherwise(
            pl.col(kolom).round(1).cast(pl.Utf8).str.replace(".", ",", literal=True)
            + "%"
        )
    )


def rendementstabel(df: pl.DataFrame, analyse) -> pl.DataFrame:
    per = ["Cohort", "Opleidingcode", "Niveau", "Leertraject", "Duur", "Duur_bron"]
    agg = ov.met_opleiding(ov.rendement_aggregeer(df, per), analyse.opleidingen)
    return agg.select(
        "Cohort",
        "Opleiding",
        "Niveau",
        pl.col("Leertraject").alias("Leerweg"),
        "Duur",
        pl.col("Duur_bron").replace({"standaard": "standaardduur"}).alias("Duur uit"),
        "Instroom",
        tekst("Nominaal_percentage").alias("Nominaal %"),
        tekst("Nominaal_plus_1_percentage").alias("Nominaal + 1 %"),
        pl.col("Nog_niet_waarneembaar").alias("Nog niet waarneembaar"),
        tekst("Uitval_1_percentage").alias("Uitval na 1 jaar %"),
        tekst("Uitval_duur_percentage").alias("Uitval na duur %"),
    ).sort("Cohort", "Opleiding", "Leerweg")


st.title("Cohorten")
analyse = ui.vereis_analyse()
resultaten = ui.resultaten(analyse)
filters = ui.filters(analyse)
ui.toon_label()

if resultaten.cohorten.is_empty():
    st.info(
        "Geen instroomcohorten gevonden: alle opleidingen begonnen vóór de eerste "
        "1 oktober in je bestanden."
    )
    ui.toon_dekkingsmeldingen(analyse)
    st.stop()

cohorten = ui.filter_toepassen(resultaten.cohorten, filters, analyse, True)
instroom = ui.filter_toepassen(resultaten.instroom, filters, analyse, True)
if cohorten.is_empty():
    st.info("Geen cohorten voor deze selectie.")
    st.stop()
ui.toon_dekkingsmeldingen(analyse)

totaal = ov.rendement_aggregeer(cohorten, ["Cohort"])

st.subheader("Instroom per cohort", help=DEFINITIES["instroomcohort"])
instroomgrafiek(instroom)
st.caption(
    "Herkomst: nieuw bij de instelling, na een diploma (stapelen), van een ander "
    "niveau zonder diploma, of een wissel van crebo op hetzelfde niveau. Een "
    "crebo-vernieuwing telt als dezelfde opleiding."
)

st.subheader(
    "Rendement per cohort",
    help=DEFINITIES["rendement_nominaal"]
    + "\n\n"
    + DEFINITIES["rendement_nominaal_plus_1"],
)
percentagegrafiek(totaal, RENDEMENT, "Rendement (%)")
st.caption(
    "Grijs = nog niet waarneembaar: voor een deel van het cohort valt de nominale "
    "duur (of een jaar meer) nog niet in je bestanden. Dat telt niet als 0%."
)

st.subheader("Uitval", help=DEFINITIES["uitval"])
percentagegrafiek(totaal, UITVAL, "Uitval (%)")

st.subheader("Per opleiding")
st.caption(
    "Duur uit: de nominale duur komt uit de geplande einddatum van de "
    "inschrijvingen, of is de standaardduur van het niveau als er te weinig "
    "inschrijvingen zijn."
)
ui.toon_tabel(rendementstabel(cohorten, analyse), "cohorten")
