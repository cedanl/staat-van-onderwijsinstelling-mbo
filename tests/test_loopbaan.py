from datetime import date

import polars as pl

from staat_mbo.loopbaan import eerste_peiljaar, niveau_getal, peilmomenten


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
