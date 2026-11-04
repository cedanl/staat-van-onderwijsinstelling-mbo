import polars as pl

from staat_mbo import overzicht as ov


def _rij(indicator, jaar, crebo, niveau, teller, noemer, volledig=True):
    return {
        "Indicator": indicator,
        "Jaartijdvak": jaar,
        "Periode": f"{jaar - 2}-{jaar - 1} t/m {jaar}-{jaar + 1}",
        "Groep": "opleiding_leerweg",
        "Opleidingcode": crebo,
        "Niveau": niveau,
        "Leertraject": "BOL",
        "Teller": teller,
        "Noemer": noemer,
        "Volledig": volledig,
    }


def _basis(*rijen):
    return pl.DataFrame(
        list(rijen),
        schema={
            "Indicator": pl.Utf8,
            "Jaartijdvak": pl.Int32,
            "Periode": pl.Utf8,
            "Groep": pl.Utf8,
            "Opleidingcode": pl.Utf8,
            "Niveau": pl.Int32,
            "Leertraject": pl.Utf8,
            "Teller": pl.Int64,
            "Noemer": pl.Int64,
            "Volledig": pl.Boolean,
        },
    )


def test_aggregeer_telt_op_en_geeft_de_norm_van_het_ene_niveau():
    basis = _basis(_rij("JR", 2024, "A", 2, 30, 40), _rij("JR", 2024, "B", 2, 45, 60))
    (rij,) = ov.aggregeer(basis, []).iter_rows(named=True)
    assert (rij["Teller"], rij["Noemer"], rij["Percentage"]) == (75, 100, 75.0)
    assert rij["Norm"] == 67  # JR niveau 2: er is maar één niveau over


def test_aggregeer_geeft_geen_norm_boven_niveau_en_geen_percentage_te_klein():
    basis = _basis(_rij("JR", 2024, "A", 2, 5, 11), _rij("JR", 2024, "B", 3, 50, 60))
    alles = ov.aggregeer(basis, [])
    assert alles["Norm"][0] is None
    per_niveau = ov.aggregeer(basis, ["Niveau"]).sort("Niveau")
    assert per_niveau["Te_klein"].to_list() == [True, False]
    assert per_niveau["Percentage"].to_list() == [None, 83.3]
    assert per_niveau["Norm"].to_list() == [67, 68]


def test_cel_toont_percentage_met_komma_icoon_of_te_weinig():
    basis = _basis(
        _rij("JR", 2024, "A", 2, 5, 11),
        _rij("JR", 2024, "B", 2, 50, 60, volledig=False),
    )
    cellen = ov.aggregeer(basis, ["Opleidingcode"]).sort("Opleidingcode")
    a, b = (ov.cel(r) for r in cellen.iter_rows(named=True))
    assert a == "te weinig studenten (n = 11)"
    assert b == "83,3% ⚠"


def test_tabel_zet_indicatoren_naast_elkaar_met_streepje_voor_ontbrekend():
    basis = _basis(_rij("JR", 2024, "A", 2, 50, 60), _rij("SR", 2024, "A", 2, 40, 50))
    agg = ov.aggregeer(ov.laatste(basis), ["Opleidingcode", "Niveau"])
    (rij,) = ov.tabel_studiesucces(agg, ["Opleidingcode", "Niveau"]).iter_rows(
        named=True
    )
    assert (rij["JR"], rij["DR"], rij["SR"]) == ("83,3%", "–", "80,0%")
    assert rij["n"] == "60 / – / 50"
    assert rij["Norm"] == "67% / – / 79%"


def test_laatste_neemt_per_indicator_het_laatste_jaar():
    basis = _basis(_rij("JR", 2023, "A", 2, 1, 2), _rij("JR", 2024, "A", 2, 1, 2))
    assert ov.laatste(basis)["Jaartijdvak"].to_list() == [2024]


def _loopbaan():
    rijen = [
        (2020, 2, "Diploma, vertrokken", 3),
        (2020, 2, "Vertrokken zonder diploma", 1),
        (2021, 2, "Zonder diploma, zelfde opleiding", 4),
    ]
    return pl.DataFrame(
        rijen, schema=["Cohort", "Niveau", "Status", "Aantal"], orient="row"
    )


def test_verdeling_telt_op_tot_100_procent_per_cohort():
    tabel = ov.verdeling_tabel(_loopbaan(), ["Cohort", "Niveau"])
    assert tabel["Totaal"].to_list() == [100.0, 100.0]
    assert tabel["n"].to_list() == [4, 4]
    assert tabel["Diploma, vertrokken"].to_list() == [75.0, 0.0]


def test_overgangsmatrix_heeft_alle_niveaus_en_weg():
    df = pl.DataFrame(
        [
            (2, "n3", True, 5),
            (2, "weg", True, 2),
            (2, "n2", False, 7),
            (3, "weg", False, 1),
        ],
        schema=["Niveau", "Naar", "Diploma", "Aantal"],
        orient="row",
    )
    alles = ov.overgangsmatrix(df)
    assert alles.columns == ["Van", "n1", "n2", "n3", "n4", "weg"]
    assert alles["Van"].to_list() == ["n1", "n2", "n3", "n4"]
    assert alles.filter(pl.col("Van") == "n2").row(0) == ("n2", 0, 7, 5, 0, 2)
    met = ov.overgangsmatrix(df, diploma=True)
    assert met.filter(pl.col("Van") == "n2")["n2"][0] == 0


def test_pct_met_komma():
    assert ov.pct(75.0) == "75,0%"
    assert ov.pct(None) == "–"
