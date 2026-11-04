import polars as pl
import pytest
from mbo_bekostiging_bestanden.indicatoren import norm_voor

from staat_mbo.indicatoren import driejaarscijfer
from tests.maak import waarneming


def _jaren(*rijen, crebo="25498", niveau=2, leertraject="BOL", extra=None):
    """Rijen: (jaartijdvak, teller, noemer)."""
    return pl.DataFrame(
        [
            {
                "Jaartijdvak": t,
                "Opleidingcode": crebo,
                "Niveau": niveau,
                "Leertraject": leertraject,
                "Teller": teller,
                "Noemer": noemer,
                **(extra or {}),
            }
            for t, teller, noemer in rijen
        ],
        schema={
            "Jaartijdvak": pl.Int32,
            "Opleidingcode": pl.Utf8,
            "Niveau": pl.Int32,
            "Leertraject": pl.Utf8,
            "Teller": pl.Int64,
            "Noemer": pl.Int64,
        },
    )


def _regeling():
    return _jaren((2020, 5, 20), (2021, 30, 40), (2022, 40, 40))


def _rij(uit, t):
    rijen = uit.filter(pl.col("Jaartijdvak") == t).to_dicts()
    assert len(rijen) == 1
    return rijen[0]


def test_normen_komen_overeen_met_de_regeling():
    assert norm_voor("sr", 2, "voldoende") == 79
    assert norm_voor("dr", 3, "voldoende") == 70
    assert norm_voor("jr", 4, "voldoende") == 68


def test_driejaarscijfer_voorbeeld_uit_de_regeling():
    uit = driejaarscijfer(
        _regeling(), "jr", waarneming(2018, 2025), "opleiding_leerweg"
    )
    rij = _rij(uit, 2022)
    assert (rij["Teller"], rij["Noemer"], rij["Percentage"]) == (75, 100, 75.0)
    assert (rij["Norm"], rij["Onder_norm"]) == (67, False)
    assert rij["Indicator"] == "JR"
    assert rij["Groep"] == "opleiding_leerweg"


def test_driejaarscijfer_alleen_perioden_met_drie_waarneembare_jaartijdvakken():
    een = _jaren((2020, 5, 20), (2021, 30, 40), (2022, 40, 40), (2023, 9, 10))
    # Waarneembaar JR: 2020 t/m 2024. 2019 mist, dus niet t/m 2021.
    uit = driejaarscijfer(een, "jr", waarneming(2020, 2025), "opleiding_leerweg")
    assert uit["Jaartijdvak"].min() == 2022


def test_driejaarscijfer_diplomaresultaat_onder_de_norm():
    een = _jaren((2020, 70, 100), (2021, 70, 100), (2022, 69, 100), niveau=3)
    een = een.with_columns(pl.col("Teller").cast(pl.Int64))
    # 209/300 = 69,67%: onder 70.
    uit = driejaarscijfer(een, "dr", waarneming(2018, 2025), "niveau")
    rij = _rij(uit, 2022)
    assert (rij["Norm"], rij["Onder_norm"]) == (70, True)
    assert rij["Percentage"] == 69.7


def test_driejaarscijfer_startersresultaat_norm_niveau_2():
    een = _jaren((2020, 80, 100), (2021, 80, 100), (2022, 80, 100))
    uit = driejaarscijfer(een, "sr", waarneming(2012, 2025), "niveau")
    assert _rij(uit, 2022)["Norm"] == 79


def test_driejaarscijfer_jaar_zonder_rij_telt_als_nul_van_nul():
    een = _jaren((2020, 5, 20), (2022, 40, 40))
    uit = driejaarscijfer(een, "jr", waarneming(2018, 2025), "opleiding_leerweg")
    rij = _rij(uit, 2022)
    assert (rij["Teller"], rij["Noemer"]) == (45, 60)


def test_driejaarscijfer_te_klein_vanaf_noemer_12():
    klein = driejaarscijfer(
        _jaren((2020, 1, 4), (2021, 1, 4), (2022, 1, 3)),
        "jr",
        waarneming(2018, 2025),
        "opleiding_leerweg",
    )
    genoeg = driejaarscijfer(
        _jaren((2020, 1, 4), (2021, 1, 4), (2022, 1, 4)),
        "jr",
        waarneming(2018, 2025),
        "opleiding_leerweg",
    )
    assert _rij(klein, 2022)["Te_klein"] is True
    assert _rij(genoeg, 2022)["Te_klein"] is False


def test_driejaarscijfer_instelling_heeft_geen_norm():
    een = pl.concat(
        [
            _jaren((2020, 5, 10), (2021, 5, 10), (2022, 5, 10)),
            _jaren(
                (2020, 8, 10), (2021, 8, 10), (2022, 8, 10), crebo="25475", niveau=3
            ),
        ]
    )
    uit = driejaarscijfer(een, "jr", waarneming(2018, 2025), "instelling")
    rij = _rij(uit, 2022)
    assert (rij["Teller"], rij["Noemer"]) == (39, 60)
    assert rij["Norm"] is None and rij["Onder_norm"] is None
    assert rij["Niveau"] is None and rij["Opleidingcode"] is None


def test_driejaarscijfer_niveau_telt_de_crebos_op():
    een = pl.concat(
        [
            _jaren((2020, 5, 10), (2021, 5, 10), (2022, 5, 10)),
            _jaren((2020, 8, 10), (2021, 8, 10), (2022, 8, 10), crebo="25225"),
            _jaren(
                (2020, 1, 10), (2021, 1, 10), (2022, 1, 10), crebo="25475", niveau=3
            ),
        ]
    )
    uit = driejaarscijfer(een, "jr", waarneming(2018, 2025), "niveau")
    n2 = _rij(uit.filter(pl.col("Niveau") == 2), 2022)
    assert (n2["Teller"], n2["Noemer"]) == (39, 60)
    assert _rij(uit.filter(pl.col("Niveau") == 3), 2022)["Noemer"] == 30


def test_driejaarscijfer_opleiding_telt_de_leerwegen_op():
    een = pl.concat(
        [
            _jaren((2020, 5, 10), (2021, 5, 10), (2022, 5, 10)),
            _jaren((2020, 5, 10), (2021, 5, 10), (2022, 5, 10), leertraject="BBL"),
        ]
    )
    uit = driejaarscijfer(een, "jr", waarneming(2018, 2025), "opleiding")
    assert _rij(uit, 2022)["Noemer"] == 60
    uit = driejaarscijfer(een, "jr", waarneming(2018, 2025), "opleiding_leerweg")
    assert uit.filter(pl.col("Jaartijdvak") == 2022)["Noemer"].to_list() == [30, 30]


def test_driejaarscijfer_volledig_jr_is_altijd_waar():
    uit = driejaarscijfer(_regeling(), "jr", waarneming(2018, 2025), "instelling")
    assert _rij(uit, 2022)["Volledig"] is True


def test_driejaarscijfer_volledig_dr_hangt_af_van_diplomahistorie():
    kort = driejaarscijfer(_regeling(), "dr", waarneming(2018, 2025), "instelling")
    lang = driejaarscijfer(_regeling(), "dr", waarneming(2010, 2025), "instelling")
    assert _rij(kort, 2022)["Volledig"] is False
    assert _rij(lang, 2022)["Volledig"] is True


def test_driejaarscijfer_volledig_sr_vraagt_terugblik_zes_in_alle_drie_jaren():
    # t = 2022 met eerste_jaar 2014: terugblik voor 2020, 2021, 2022 is 6.
    lang = driejaarscijfer(_regeling(), "sr", waarneming(2014, 2025), "instelling")
    kort = driejaarscijfer(_regeling(), "sr", waarneming(2015, 2025), "instelling")
    assert _rij(lang, 2022)["Volledig"] is True
    assert _rij(kort, 2022)["Volledig"] is False


def test_driejaarscijfer_periodelabel():
    uit = driejaarscijfer(_regeling(), "jr", waarneming(2018, 2025), "instelling")
    assert _rij(uit, 2022)["Periode"] == "2020-2021 t/m 2022-2023"


def test_driejaarscijfer_onbekende_groep_geeft_een_fout():
    with pytest.raises(ValueError):
        driejaarscijfer(_regeling(), "jr", waarneming(2018, 2025), "kwartaal")


def test_driejaarscijfer_heeft_het_afgesproken_schema():
    uit = driejaarscijfer(_regeling(), "jr", waarneming(2018, 2025), "instelling")
    assert uit.columns == [
        "Indicator",
        "Jaartijdvak",
        "Periode",
        "Groep",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "Teller",
        "Noemer",
        "Percentage",
        "Norm",
        "Onder_norm",
        "Te_klein",
        "Volledig",
    ]
