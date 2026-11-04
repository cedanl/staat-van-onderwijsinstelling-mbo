from datetime import date

import polars as pl

from staat_mbo.loopbaan import (
    diplomas,
    eerste_peiljaar,
    jaartijdvak,
    niveau_getal,
    peilmomenten,
)


def _waarde(expr, **kolommen):
    return pl.DataFrame(kolommen).select(expr.alias("x"))["x"].to_list()


def _sj(*rijen):
    """Rijen: (persoon, jaar, crebo, niveau, begin, brin, volgnr)."""
    return {
        "fact_inschrijving_schooljaar": pl.DataFrame(
            [
                {
                    "BRIN": brin,
                    "_persoon_id": persoon,
                    "Inschrijvingvolgnummer": volgnr,
                    "Schooljaar": jaar,
                    "DatumBegin": begin,
                    "Opleidingcode": crebo,
                    "Niveau": niveau,
                    "Leertraject": "BOL",
                    "_hoofdinschrijving": False,
                }
                for persoon, jaar, crebo, niveau, begin, brin, volgnr in rijen
            ],
            schema={
                "BRIN": pl.Utf8,
                "_persoon_id": pl.Utf8,
                "Inschrijvingvolgnummer": pl.Utf8,
                "Schooljaar": pl.Int32,
                "DatumBegin": pl.Date,
                "Opleidingcode": pl.Utf8,
                "Niveau": pl.Utf8,
                "Leertraject": pl.Utf8,
                "_hoofdinschrijving": pl.Boolean,
            },
        )
    }


def _r(persoon, jaar, crebo, niveau, begin=date(2022, 8, 1), brin="A", volgnr="1"):
    return (persoon, jaar, crebo, niveau, begin, brin, volgnr)


def test_eerste_peiljaar():
    d = [date(2022, 8, 1), date(2022, 10, 1), date(2022, 10, 2)]
    assert _waarde(eerste_peiljaar(pl.col("d")), d=d) == [2022, 2022, 2023]


def test_niveau_getal():
    assert _waarde(niveau_getal(pl.col("n")), n=["MBO-3", None]) == [3, None]


def test_hoogste_niveau_over_brins_wint():
    star = _sj(
        _r("s1", 2022, "25498", "MBO-2", brin="A"),
        _r("s1", 2022, "25475", "MBO-3", brin="B"),
    )
    df = peilmomenten(star)
    assert df.height == 1
    rij = df.row(0, named=True)
    assert (rij["Niveau"], rij["BRIN"], rij["Opleidingcode"]) == (3, "B", "25475")


def test_gelijk_niveau_laagste_crebo():
    star = _sj(
        _r("s1", 2022, "25475", "MBO-3"),
        _r("s1", 2022, "25191", "MBO-3", volgnr="2"),
    )
    assert peilmomenten(star)["Opleidingcode"].to_list() == ["25191"]


def test_gelijk_niveau_en_crebo_recentste_begin():
    star = _sj(
        _r("s1", 2022, "25191", "MBO-3", begin=date(2021, 8, 1)),
        _r("s1", 2022, "25191", "MBO-3", begin=date(2022, 8, 1), volgnr="2"),
    )
    assert peilmomenten(star)["DatumBegin"].to_list() == [date(2022, 8, 1)]


def test_zonder_niveau_telt_als_aanwezig():
    df = peilmomenten(_sj(_r("s1", 2022, "99999", None)))
    assert df.height == 1
    assert df["Niveau"].to_list() == [None]


def test_inschrijving_met_niveau_gaat_voor_zonder():
    star = _sj(
        _r("s1", 2022, "99999", None),
        _r("s1", 2022, "25498", "MBO-2", volgnr="2"),
    )
    assert peilmomenten(star)["Opleidingcode"].to_list() == ["25498"]


def test_ontbrekend_niveau_wordt_aangevuld_uit_referentiedata():
    df = peilmomenten(_sj(_r("s1", 2022, "25498", None)))
    assert df["Niveau"].to_list() == [2]


def test_twee_jaren_twee_rijen_met_type_i32():
    star = _sj(_r("s1", 2022, "25498", "MBO-2"), _r("s1", 2023, "25498", "MBO-2"))
    df = peilmomenten(star)
    assert df.height == 2
    assert df.schema["Jaar"] == pl.Int32
    assert df.schema["Niveau"] == pl.Int32
    assert sorted(df["Jaar"].to_list()) == [2022, 2023]


def test_uniek_per_persoon_en_jaar():
    star = _sj(
        _r("s1", 2022, "25498", "MBO-2", brin="A"),
        _r("s1", 2022, "25498", "MBO-2", brin="B"),
        _r("s2", 2022, "25475", "MBO-3"),
        _r("s2", 2023, "25475", "MBO-3"),
    )
    df = peilmomenten(star)
    assert not df.select("_persoon_id", "Jaar").is_duplicated().any()
    assert df.columns == [
        "_persoon_id",
        "Jaar",
        "BRIN",
        "Inschrijvingvolgnummer",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "DatumBegin",
    ]


def test_v4_functies_die_we_gebruiken_bestaan_nog():
    """Faalt bij een v4-upgrade die deze interne functies weghaalt."""
    from mbo_bekostiging_bestanden.opleidingsniveau import vul_niveau_aan
    from mbo_bekostiging_bestanden.waardenlijsten import (
        leertrajecten_buiten_indicatorpopulatie,
    )

    assert callable(vul_niveau_aan)
    assert {"OVO", "ODT"} <= set(leertrajecten_buiten_indicatorpopulatie())


def _dip_star(inschrijvingen, opleidingen=None):
    """Inschrijvingen: (persoon, crebo van inschrijving, diploma-crebo, datum)."""
    ins = pl.DataFrame(
        [
            {
                "_persoon_id": persoon,
                "BRIN": "27DV",
                "Opleidingcode": crebo,
                "Leertraject": "BBL",
                "DIP_Opleidingcode": dip,
                "DIP_DatumResultaat": datum,
            }
            for persoon, crebo, dip, datum in inschrijvingen
        ],
        schema={
            "_persoon_id": pl.Utf8,
            "BRIN": pl.Utf8,
            "Opleidingcode": pl.Utf8,
            "Leertraject": pl.Utf8,
            "DIP_Opleidingcode": pl.Utf8,
            "DIP_DatumResultaat": pl.Date,
        },
    )
    opl = opleidingen or {"25498": "MBO-2", "25475": "MBO-3"}
    return {
        "fact_inschrijving": ins,
        "dim_opleiding": pl.DataFrame(
            {"Opleidingcode": list(opl), "Niveau": list(opl.values())},
            schema={"Opleidingcode": pl.Utf8, "Niveau": pl.Utf8},
        ),
    }


def test_jaartijdvak_grens_op_1_oktober():
    d = [date(2024, 9, 30), date(2024, 10, 1)]
    assert _waarde(jaartijdvak(pl.col("d")), d=d) == [2023, 2024]


def test_diploma_krijgt_jaartijdvak():
    star = _dip_star(
        [
            ("s1", "25498", "25498", date(2024, 9, 30)),
            ("s2", "25498", "25498", date(2024, 10, 1)),
        ]
    )
    df = diplomas(star).sort("_persoon_id")
    assert df["Jaartijdvak"].to_list() == [2023, 2024]
    assert df.schema["Jaartijdvak"] == pl.Int32


def test_zelfde_diploma_op_drie_periode_rijen_is_een_rij():
    rij = ("s1", "25498", "25498", date(2023, 6, 30))
    assert diplomas(_dip_star([rij, rij, rij])).height == 1


def test_niveau_is_dat_van_het_diploma_niet_van_de_inschrijving():
    star = _dip_star([("s1", "25475", "25498", date(2023, 6, 30))])
    rij = diplomas(star).row(0, named=True)
    assert rij["Niveau"] == 2
    assert rij["Opleidingcode"] == "25498"


def test_niveau_zonder_dim_opleiding_via_referentiedata():
    star = _dip_star(
        [
            ("s1", "25475", "25498", date(2023, 6, 30)),
            ("s2", "25475", "99999", date(2023, 6, 30)),
        ],
        opleidingen={"25475": "MBO-3"},
    )
    df = diplomas(star).sort("_persoon_id")
    assert df["Niveau"].to_list() == [2, None]


def test_leertraject_en_brin_van_de_inschrijving():
    rij = diplomas(_dip_star([("s1", "25498", "25498", date(2023, 6, 30))])).row(
        0, named=True
    )
    assert (rij["Leertraject"], rij["BRIN"]) == ("BBL", "27DV")


def test_zonder_diplomadatum_valt_weg():
    star = _dip_star([("s1", "25498", None, None), ("s2", "25498", "25498", None)])
    assert diplomas(star).is_empty()


def test_diplomas_schema():
    df = diplomas(_dip_star([("s1", "25498", "25498", date(2023, 6, 30))]))
    assert df.columns == [
        "_persoon_id",
        "Opleidingcode",
        "Niveau",
        "Leertraject",
        "BRIN",
        "Datum",
        "Jaartijdvak",
    ]
    assert df.schema["Niveau"] == pl.Int32
