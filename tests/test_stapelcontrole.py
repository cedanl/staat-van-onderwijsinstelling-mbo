from datetime import date

import polars as pl

from staat_mbo.stapelcontrole import controleer_stapel


def _star(
    leveringen,
    jaren=(2020, 2021, 2022, 2023, 2024),
    namen=("Curio",),
    laatste=None,
):
    return {
        "fact_inschrijving_schooljaar": pl.DataFrame(
            {
                "BRIN": ["21CY"] * len(jaren),
                "_persoon_id": [f"p{j}" for j in jaren],
                "Schooljaar": list(jaren),
            },
            schema={"BRIN": pl.Utf8, "_persoon_id": pl.Utf8, "Schooljaar": pl.Int32},
        ),
        "meta_leveringen": _leveringen(leveringen, laatste),
        "dim_instelling": pl.DataFrame(
            {
                "BRIN": [f"B{i}" for i in range(len(namen))],
                "Instelling_naam": list(namen),
            }
        ),
    }


def _leveringen(rijen, laatste):
    df = pl.DataFrame(
        rijen,
        schema={
            "levering": pl.Utf8,
            "BRIN": pl.Utf8,
            "DatumBeginPeriode": pl.Date,
            "DatumEindePeriode": pl.Date,
        },
        orient="row",
    )
    peil = laatste or [date(2024, 10, 1)] * df.height
    return df.with_columns(pl.Series("Laatste_peildatum", peil, dtype=pl.Date))


def test_aansluitende_leveringen_geen_gat():
    r = controleer_stapel(
        _star(
            [
                ("a", "21CY", date(2020, 8, 1), date(2022, 7, 31)),
                ("b", "21CY", date(2022, 8, 1), date(2024, 7, 31)),
            ]
        )
    )
    assert r.ok and r.gaten == [] and r.waarschuwingen == []
    assert r.schooljaren == [2020, 2021, 2022, 2023, 2024]
    assert r.aantal_studenten == 5


def test_gat_tussen_leveringen_is_waarschuwing():
    r = controleer_stapel(
        _star(
            [
                ("a", "21CY", date(2020, 8, 1), date(2021, 7, 31)),
                ("b", "21CY", date(2022, 8, 1), date(2024, 7, 31)),
            ]
        )
    )
    assert r.ok
    assert r.gaten == [{"brin": "21CY", "na": "2021-07-31", "voor": "2022-08-01"}]
    assert any("gat" in w for w in r.waarschuwingen)


def test_tbgi_levering_zonder_periode_telt_niet_mee():
    r = controleer_stapel(
        _star(
            [
                ("a", "21CY", date(2020, 8, 1), date(2024, 7, 31)),
                ("t", None, None, None),
            ]
        )
    )
    assert r.gaten == []


def test_meerdere_instellingen_waarschuwing():
    r = controleer_stapel(
        _star(
            [("a", "21CY", date(2020, 8, 1), date(2024, 7, 31))],
            namen=("Curio", "ROC X"),
        )
    )
    assert any("één bestuur" in w for w in r.waarschuwingen)


def test_weinig_jaren_waarschuwing():
    r = controleer_stapel(
        _star([("a", "21CY", date(2023, 8, 1), date(2024, 7, 31))], jaren=(2023, 2024))
    )
    assert any("5 jaar" in w for w in r.waarschuwingen)


def test_lege_data_is_fout():
    star = _star([("a", "21CY", date(2020, 8, 1), date(2024, 7, 31))], jaren=())
    r = controleer_stapel(star)
    assert not r.ok
    assert r.meldingen()[0].startswith("Niet gelukt")


def test_meldingen_beginnen_met_resultaat():
    r = controleer_stapel(_star([("a", "21CY", date(2020, 8, 1), date(2024, 7, 31))]))
    assert r.meldingen()[0].startswith("Gelukt")


def test_demo_stapel(demo_star):
    star, _ = demo_star
    r = controleer_stapel(star)
    assert r.ok
    assert r.brins == ["21CY", "25LX", "27DV"]


def test_brins_met_ander_einde_waarschuwing():
    r = controleer_stapel(
        _star(
            [
                ("a", "21CY", date(2020, 8, 1), date(2024, 7, 31)),
                ("b", "25LX", date(2020, 8, 1), date(2025, 7, 31)),
            ],
            laatste=[date(2023, 10, 1), date(2024, 10, 1)],
        )
    )
    assert any("21CY" in w and "uitval" in w for w in r.waarschuwingen)
