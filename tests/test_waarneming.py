from datetime import date

import polars as pl
import pytest

from staat_mbo.waarneming import Waarneming, waarneming


def _star(*leveringen):
    """Leveringen: (brin, begin, einde, laatste_peildatum); begin None = TBG-i."""
    meta = pl.DataFrame(
        leveringen,
        schema={
            "BRIN": pl.Utf8,
            "DatumBeginPeriode": pl.Date,
            "DatumEindePeriode": pl.Date,
            "Laatste_peildatum": pl.Date,
        },
        orient="row",
    )
    return {"meta_leveringen": meta}


def test_een_brin():
    w = waarneming(_star(("A", date(2020, 8, 1), date(2026, 7, 31), date(2025, 10, 1))))
    assert (w.eerste_jaar, w.laatste_jaar) == (2020, 2025)
    assert w.diplomas_vanaf == date(2020, 8, 1)
    assert w.gaten == []


def test_laatste_jaar_is_het_vroegste_einde():
    w = waarneming(
        _star(
            ("A", date(2020, 8, 1), date(2026, 7, 31), date(2025, 10, 1)),
            ("B", date(2020, 8, 1), date(2025, 7, 31), date(2024, 10, 1)),
        )
    )
    assert w.laatste_jaar == 2024


def test_eerste_jaar_is_het_laatste_begin():
    w = waarneming(
        _star(
            ("A", date(2018, 8, 1), date(2026, 7, 31), date(2025, 10, 1)),
            ("B", date(2020, 8, 1), date(2026, 7, 31), date(2025, 10, 1)),
        )
    )
    assert w.eerste_jaar == 2020
    assert w.diplomas_vanaf == date(2018, 8, 1)


def test_begin_na_1_oktober_geeft_het_volgende_jaar():
    w = waarneming(
        _star(("A", date(2020, 10, 2), date(2026, 7, 31), date(2025, 10, 1)))
    )
    assert w.eerste_jaar == 2021


def test_gat_tussen_leveringen():
    w = waarneming(
        _star(
            ("A", date(2020, 8, 1), date(2022, 7, 31), date(2025, 10, 1)),
            ("A", date(2023, 8, 1), date(2025, 7, 31), date(2025, 10, 1)),
        )
    )
    assert w.gaten == [2022]
    assert w.waarneembaar(2022) is False
    assert w.reeks(2021, 2023) is False
    assert w.reeks(2023, 2024) is True


def test_levering_zonder_begin_telt_niet_mee_voor_eerste_jaar():
    w = waarneming(
        _star(
            ("A", date(2020, 8, 1), date(2026, 7, 31), date(2025, 10, 1)),
            (None, None, None, date(2025, 10, 1)),
        )
    )
    assert w.eerste_jaar == 2020


def test_niet_waarneembaar_voor_het_eerste_jaar():
    w = waarneming(_star(("A", date(2020, 8, 1), date(2026, 7, 31), date(2025, 10, 1))))
    assert w.waarneembaar(2019) is False
    assert w.waarneembaar(2020) is True
    assert w.waarneembaar(2026) is False


def test_zonder_ro_is_een_fout():
    with pytest.raises(ValueError):
        waarneming(_star((None, None, None, date(2025, 10, 1))))


def test_demodata(demodata_star):
    w = waarneming(demodata_star)
    assert isinstance(w, Waarneming)
    assert w.eerste_jaar <= w.laatste_jaar


def test_fixtures_geven_een_waarneming(demo_star):
    star, _ = demo_star
    assert isinstance(waarneming(star), Waarneming)
