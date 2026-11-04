"""Overzichten voor de app: filteren, samentellen en opmaken van de tabellen.

Alles werkt op de geaggregeerde tabellen van ``analyse.bereken`` (nooit op
studentniveau) en kent geen Streamlit, zodat het los te testen is.
"""

from dataclasses import dataclass

import polars as pl
from mbo_bekostiging_bestanden.indicatoren import norm_voor

from staat_mbo.cohorten import CATEGORIEEN
from staat_mbo.indicatoren import MIN_NOEMER, NIVEAUS

INDICATOREN = ["JR", "DR", "SR"]
ONVOLLEDIG = "⚠"
TE_KLEIN = "te weinig studenten"
NOG_NIET = "nog niet waarneembaar"
_NORMEN = pl.DataFrame(
    [
        {"Indicator": i.upper(), "_n": n, "Norm": norm_voor(i, n, "voldoende")}
        for i in ("jr", "dr", "sr")
        for n in NIVEAUS
    ],
    schema={"Indicator": pl.Utf8, "_n": pl.Int32, "Norm": pl.Int64},
)


def pct(waarde: float | None) -> str:
    """Percentage met een komma: ``75.0`` wordt ``"75,0%"``."""
    return "–" if waarde is None else f"{waarde:.1f}".replace(".", ",") + "%"


@dataclass(frozen=True)
class Filters:
    """Keuzes uit de zijbalk; een lege lijst betekent "alles"."""

    niveaus: tuple[int, ...] = ()
    leerwegen: tuple[str, ...] = ()
    domeinen: tuple[str, ...] = ()
    opleidingen: tuple[str, ...] = ()  # crebo's

    @property
    def actief(self) -> bool:
        return any((self.niveaus, self.leerwegen, self.domeinen, self.opleidingen))


def toepassen(df: pl.DataFrame, f: Filters, opleidingen: pl.DataFrame) -> pl.DataFrame:
    """Filter een tabel met ``Opleidingcode``, ``Niveau`` en ``Leertraject``."""
    if f.niveaus:
        df = df.filter(pl.col("Niveau").is_in(f.niveaus))
    if f.leerwegen:
        df = df.filter(pl.col("Leertraject").is_in(f.leerwegen))
    if f.domeinen:
        codes = opleidingen.filter(pl.col("Opleiding_domein").is_in(f.domeinen))[
            "Opleidingcode"
        ]
        df = df.filter(pl.col("Opleidingcode").is_in(codes.to_list()))
    if f.opleidingen:
        df = df.filter(pl.col("Opleidingcode").is_in(f.opleidingen))
    return df


def met_opleiding(df: pl.DataFrame, opleidingen: pl.DataFrame) -> pl.DataFrame:
    """Voeg ``Opleiding`` ("Naam (crebo)") toe; zonder naam alleen het crebo."""
    namen = opleidingen.select(
        "Opleidingcode",
        pl.when(pl.col("Opleiding_naam").is_not_null())
        .then(
            pl.concat_str(
                pl.col("Opleiding_naam"),
                pl.lit(" ("),
                pl.col("Opleidingcode"),
                pl.lit(")"),
            )
        )
        .otherwise(pl.col("Opleidingcode"))
        .alias("Opleiding"),
    )
    return df.join(namen, on="Opleidingcode", how="left").with_columns(
        pl.col("Opleiding").fill_null(pl.col("Opleidingcode"))
    )


# --- Studiesucces -----------------------------------------------------------


def laatste(df: pl.DataFrame) -> pl.DataFrame:
    """Per indicator alleen de laatste periode."""
    return df.filter(
        pl.col("Jaartijdvak") == pl.col("Jaartijdvak").max().over("Indicator")
    )


def aggregeer(df: pl.DataFrame, sleutel: list[str]) -> pl.DataFrame:
    """Tel de driejaarscijfers van ``opleiding_leerweg`` op tot ``sleutel``.

    De norm hoort bij het niveau: staat ``Niveau`` niet in de sleutel maar is er
    maar één niveau over, dan geldt de norm daarvan. Onder de minimale noemer is
    ``Percentage`` leeg.
    """
    kolommen = [
        "Indicator",
        "Jaartijdvak",
        "Periode",
        *sleutel,
        "Teller",
        "Noemer",
        "Percentage",
        "Norm",
        "Te_klein",
        "Volledig",
    ]
    schema = {
        "Indicator": pl.Utf8,
        "Jaartijdvak": pl.Int32,
        "Periode": pl.Utf8,
        "Opleidingcode": pl.Utf8,
        "Niveau": pl.Int32,
        "Leertraject": pl.Utf8,
        "Teller": pl.Int64,
        "Noemer": pl.Int64,
        "Percentage": pl.Float64,
        "Norm": pl.Int64,
        "Te_klein": pl.Boolean,
        "Volledig": pl.Boolean,
    }
    if df.is_empty():
        return pl.DataFrame(schema={k: schema[k] for k in kolommen})
    een_niveau = df["Niveau"].n_unique() == 1 and df["Niveau"][0] is not None
    niveau = (
        pl.col("Niveau")
        if "Niveau" in sleutel
        else pl.lit(df["Niveau"][0] if een_niveau else None, dtype=pl.Int32)
    )
    return (
        df.group_by(["Indicator", "Jaartijdvak", "Periode", *sleutel])
        .agg(
            pl.col("Teller").sum(),
            pl.col("Noemer").sum(),
            pl.col("Volledig").all(),
        )
        .with_columns(niveau.alias("_n"))
        .join(_NORMEN, on=["Indicator", "_n"], how="left")
        .with_columns(
            (pl.col("Noemer") < MIN_NOEMER).alias("Te_klein"),
            (pl.col("Teller") / pl.col("Noemer") * 100).round(1).alias("Percentage"),
        )
        .with_columns(
            pl.when(~pl.col("Te_klein")).then(pl.col("Percentage")).alias("Percentage")
        )
        .select(kolommen)
        .sort(["Indicator", "Jaartijdvak", *sleutel], nulls_last=True)
    )


def cel(rij: dict) -> str:
    """Tekst van één cijfer: percentage, of "te weinig studenten (n = …)"."""
    if rij["Te_klein"]:
        return f"{TE_KLEIN} (n = {rij['Noemer']})"
    return pct(rij["Percentage"]) + ("" if rij["Volledig"] else f" {ONVOLLEDIG}")


def tabel_studiesucces(agg: pl.DataFrame, sleutel: list[str]) -> pl.DataFrame:
    """Eén rij per groep met JR, DR en SR als tekst, n en de norm per indicator."""
    groepen: dict[tuple, dict] = {}
    for rij in agg.iter_rows(named=True):
        sleutelwaarde = tuple(rij[k] for k in sleutel)
        groep = groepen.setdefault(
            sleutelwaarde, {**dict(zip(sleutel, sleutelwaarde, strict=True))}
        )
        groep[rij["Indicator"]] = rij
    uit = []
    for groep in groepen.values():
        cellen = {i: groep.get(i) for i in INDICATOREN}
        uit.append(
            {
                **{k: v for k, v in groep.items() if k not in INDICATOREN},
                **{i: cel(r) if r else "–" for i, r in cellen.items()},
                "n": " / ".join(
                    str(r["Noemer"]) if r else "–" for r in cellen.values()
                ),
                "Norm": " / ".join(
                    f"{r['Norm']}%" if r and r["Norm"] is not None else "–"
                    for r in cellen.values()
                ),
            }
        )
    schema = {k: agg.schema[k] for k in sleutel}
    return pl.DataFrame(
        uit,
        schema={
            **schema,
            "JR": pl.Utf8,
            "DR": pl.Utf8,
            "SR": pl.Utf8,
            "n": pl.Utf8,
            "Norm": pl.Utf8,
        },
    )


# --- Cohorten ---------------------------------------------------------------


def rendement_aggregeer(df: pl.DataFrame, per: list[str]) -> pl.DataFrame:
    """Tel de cohorttabel op tot ``per``; percentages over de waarneembare rijen."""
    if df.is_empty():
        return df
    tellers = {
        "Nominaal": ("Nominaal_aantal", "N_nominaal"),
        "Nominaal_plus_1": ("Nominaal_plus_1_aantal", "N_nominaal_plus_1"),
        "Uitval_1": ("Uitval_1_aantal", "N_uitval_1"),
        "Uitval_duur": ("Uitval_duur_aantal", "N_uitval_duur"),
    }
    uit = df.group_by(per, maintain_order=True).agg(
        pl.col("Instroom").sum(),
        pl.col("Nog_niet_waarneembaar").sum(),
        *(pl.col(c).sum() for pair in tellers.values() for c in pair),
    )
    return uit.with_columns(
        *(
            pl.when(pl.col(n) > 0)
            .then((pl.col(a) / pl.col(n) * 100).round(1))
            .alias(f"{naam}_percentage")
            for naam, (a, n) in tellers.items()
        )
    ).sort(per)


def instroom_per_cohort(df: pl.DataFrame) -> pl.DataFrame:
    """Instroom per cohort × herkomst."""
    return (
        df.group_by(["Cohort", "Herkomst"])
        .agg(pl.col("Aantal").sum())
        .sort("Cohort", "Herkomst")
    )


# --- Loopbanen --------------------------------------------------------------


def verdeling(df: pl.DataFrame, per: list[str]) -> pl.DataFrame:
    """Aantal en percentage per ``per`` × loopbaanstatus (tot 100% per ``per``)."""
    return (
        df.group_by([*per, "Status"])
        .agg(pl.col("Aantal").sum())
        .with_columns(
            (pl.col("Aantal") / pl.col("Aantal").sum().over(per) * 100).alias(
                "Percentage"
            )
        )
        .sort(per)
    )


def verdeling_tabel(df: pl.DataFrame, per: list[str]) -> pl.DataFrame:
    """Percentage per loopbaanstatus naast elkaar, met een totaal en n per rij."""
    v = verdeling(df, per)
    breed = v.pivot(on="Status", index=per, values="Percentage").sort(per)
    status = [c for c in CATEGORIEEN if c in breed.columns]
    n = v.group_by(per).agg(pl.col("Aantal").sum().alias("n"))
    return (
        breed.join(n, on=per)
        .with_columns(*(pl.col(c).fill_null(0.0).round(1) for c in status))
        .with_columns(pl.sum_horizontal(status).round(0).alias("Totaal"))
        .select([*per, "n", *status, "Totaal"])
        .sort(per)
    )


def overgangsmatrix(df: pl.DataFrame, diploma: bool | None = None) -> pl.DataFrame:
    """Niveau op 1-10-t (rijen) naar het niveau een jaar later (kolommen)."""
    if diploma is not None:
        df = df.filter(pl.col("Diploma") == diploma)
    kolommen = ["n1", "n2", "n3", "n4", "weg"]
    if (df["Naar"] == "onbekend").any():
        kolommen.append("onbekend")
    breed = (
        df.with_columns(pl.concat_str(pl.lit("n"), pl.col("Niveau")).alias("Van"))
        .group_by(["Van", "Naar"])
        .agg(pl.col("Aantal").sum())
        .pivot(on="Naar", index="Van", values="Aantal")
    )
    leeg = pl.DataFrame({"Van": ["n1", "n2", "n3", "n4"]})
    uit = leeg.join(breed, on="Van", how="left")
    for k in kolommen:
        if k not in uit.columns:
            uit = uit.with_columns(pl.lit(None, dtype=pl.UInt32).alias(k))
    return uit.select("Van", *kolommen).with_columns(
        pl.col(k).fill_null(0).cast(pl.Int64) for k in kolommen
    )
