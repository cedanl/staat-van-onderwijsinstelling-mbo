from datetime import date

import polars as pl
import pytest

from staat_mbo import indicatoren as ind
from staat_mbo.analyse import Analyse, studiesucces
from staat_mbo.stapelcontrole import Stapelrapport
from tests.maak import diplomas, peilmomenten, waarneming

KAART = {"25498": "25999"}
FUNCTIES = {
    "jr": ind.jaarresultaat,
    "dr": ind.diplomaresultaat,
    "sr": ind.startersresultaat,
}


def _scenario():
    """Eén opleiding die in 2021 van crebo wisselt: oud 25498, opvolger 25999."""
    pm = peilmomenten(
        [
            ("s20", 2020, "25498", 2, "BOL"),
            ("s21", 2021, "25999", 2, "BOL"),
            ("s22", 2022, "25999", 2, "BOL"),
        ]
    )
    return pm, diplomas([]), waarneming(2018, 2023)


def _groepen(uit):
    return uit.filter(pl.col("Jaartijdvak") == 2022)


@pytest.mark.parametrize("indicator", FUNCTIES)
def test_zonder_opvolgers_zijn_het_twee_opleidingen(indicator):
    pm, dip, w = _scenario()
    uit = FUNCTIES[indicator](pm, dip, w)
    assert set(uit["Opleidingcode"]) == {"25498", "25999"}
    cijfer = ind.driejaarscijfer(uit, indicator, w, "opleiding_leerweg")
    assert cijfer.filter(pl.col("Jaartijdvak") == 2022).height == 2


@pytest.mark.parametrize("indicator", FUNCTIES)
def test_vernieuwd_crebo_is_een_groep_in_het_driejaarscijfer(indicator):
    pm, dip, w = _scenario()
    uit = FUNCTIES[indicator](pm, dip, w, KAART)
    assert set(uit["Opleidingcode"]) == {"25999"}
    cijfer = ind.driejaarscijfer(uit, indicator, w, "opleiding_leerweg")
    rij = cijfer.filter(pl.col("Jaartijdvak") == 2022).to_dicts()
    assert len(rij) == 1
    assert rij[0]["Opleidingcode"] == "25999"
    assert rij[0]["Noemer"] == 3


def test_jr_telt_diploma_op_oud_crebo_bij_de_opvolger():
    pm = peilmomenten(
        [("s1", 2021, "25498", 2, "BOL"), ("s2", 2021, "25999", 2, "BOL")]
    )
    dip = diplomas(
        [
            ("s1", "25498", 2, date(2022, 6, 30)),
            ("s2", "25999", 2, date(2022, 6, 30)),
        ]
    )
    uit = ind.jaarresultaat(pm, dip, waarneming(2020, 2023), KAART)
    rij = uit.filter(pl.col("Jaartijdvak") == 2021).to_dicts()
    assert [(r["Opleidingcode"], r["Teller"], r["Noemer"]) for r in rij] == [
        ("25999", 2, 2)
    ]


def test_studiesucces_gebruikt_de_opvolgers_van_de_analyse():
    pm, dip, w = _scenario()
    a = Analyse(
        rapport=Stapelrapport([], [], [], 0),
        waarneming=w,
        peilmomenten=pm,
        diplomas=dip,
        opvolgers=KAART,
    )
    uit = studiesucces(a).filter(pl.col("Groep") == "opleiding_leerweg")
    assert set(uit["Opleidingcode"]) == {"25999"}
