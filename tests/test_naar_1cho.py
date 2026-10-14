from datetime import date

import polars as pl

from staat_mbo.naar_1cho import (
    KOLOMMEN_1CHO,
    LABEL_DIPLOMA,
    LABEL_HOOFD,
    LABEL_NEVEN,
    diplomajaar,
    eerste_peiljaar,
    leeftijd_op_1_oktober,
    naar_1cho,
)


def _waarde(expr, **kolommen):
    return pl.DataFrame(kolommen).select(expr.alias("x"))["x"].to_list()


def test_eerste_peiljaar():
    d = [date(2022, 8, 1), date(2022, 10, 1), date(2022, 10, 2)]
    assert _waarde(eerste_peiljaar(pl.col("d")), d=d) == [2022, 2022, 2023]


def test_diplomajaar_venster_oktober_september():
    d = [date(2024, 9, 30), date(2024, 10, 1)]
    assert _waarde(diplomajaar(pl.col("d")), d=d) == [2023, 2024]


def test_leeftijd_op_1_oktober():
    geb = [date(2004, 10, 1), date(2004, 10, 2)]
    uit = _waarde(
        leeftijd_op_1_oktober(pl.col("g"), pl.col("j")), g=geb, j=[2022, 2022]
    )
    assert uit == [18, 17]


def _star(schooljaar_rijen, inschrijvingen, deelnemers=None):
    """Kleine star; rijen: (brin, persoon, volgnr, jaar, begin, crebo, niveau, hoofd)."""
    sj = pl.DataFrame(
        schooljaar_rijen,
        schema=[
            "BRIN",
            "_persoon_id",
            "Inschrijvingvolgnummer",
            "Schooljaar",
            "DatumBegin",
            "Opleidingcode",
            "Niveau",
            "_hoofdinschrijving",
        ],
        orient="row",
    ).with_columns(
        pl.lit("BOL").alias("Leertraject"), pl.col("Schooljaar").cast(pl.Int32)
    )
    ins = pl.DataFrame(
        inschrijvingen,
        schema={
            "_persoon_id": pl.Utf8,
            "Opleidingcode": pl.Utf8,
            "DatumInschrijving": pl.Date,
            "DatumBegin": pl.Date,
            "DIP_DatumResultaat": pl.Date,
            "DIP_Opleidingcode": pl.Utf8,
        },
        orient="row",
    )
    personen = sorted(set(sj["_persoon_id"]))
    return {
        "fact_inschrijving_schooljaar": sj,
        "fact_inschrijving": ins,
        "dim_deelnemer": deelnemers
        if deelnemers is not None
        else pl.DataFrame(
            {
                "_persoon_id": personen,
                "Geboortedatum": [date(2004, 3, 1)] * len(personen),
                "Geslacht": ["V"] * len(personen),
            }
        ),
        "dim_opleiding": pl.DataFrame(
            {
                "Opleidingcode": ["25711", "25916"],
                "Opleiding_naam": ["Kok", "Bakker"],
                "Opleiding_domein": ["Horeca", "Voedsel"],
            }
        ),
        "dim_instelling": pl.DataFrame(
            {"BRIN": ["21CY", "25LX"], "Instelling_naam": ["Curio", "Curio"]}
        ),
    }


def test_kolommen_en_vaste_waarden():
    star = _star(
        [("21CY", "p1", "1", 2021, date(2021, 8, 1), "25711", "MBO-3", True)],
        [("p1", "25711", date(2021, 8, 1), date(2021, 8, 1), None, None)],
    )
    df = naar_1cho(star)
    assert df.columns == KOLOMMEN_1CHO
    rij = df.row(0, named=True)
    assert rij["soort_hoger_onderwijs"] == "mbo"
    assert rij["soort_inschrijving_actuele_instelling"] == LABEL_HOOFD
    assert rij["type_hoger_onderwijs_binnen_soort_hoger_onderwijs"] == "niveau 3"
    assert rij["geslacht"] == "vrouw"
    assert rij["leeftijd_per_peildatum_1_oktober"] == 17
    assert rij["vestigingsnummer_gemeentenaam_volgens_rio"] == "21CY Curio"
    assert rij["opleidingscode_naam_opleiding"] == "Kok"
    assert rij["croho_onderdeel_actuele_opleiding"] == "Horeca"


def test_verblijfsjaar_telt_vanaf_start_voor_de_ro():
    # Start in 2019, RO dekt alleen 2021: verblijfsjaar 3.
    star = _star(
        [("21CY", "p1", "1", 2021, date(2021, 8, 1), "25711", "MBO-3", True)],
        [("p1", "25711", date(2019, 8, 1), date(2019, 8, 1), None, None)],
    )
    rij = naar_1cho(star).row(0, named=True)
    assert rij["verblijfsjaar_actuele_instelling"] == 3
    assert rij["verblijfsjaar_actuele_opleiding_instelling"] == 3


def test_overstap_binnen_bestuur_loopt_door():
    # 2021 op 21CY, 2022 op 25LX in een andere opleiding.
    star = _star(
        [
            ("21CY", "p1", "1", 2021, date(2021, 8, 1), "25711", "MBO-3", True),
            ("25LX", "p1", "C1", 2022, date(2022, 8, 1), "25916", "MBO-4", True),
        ],
        [
            ("p1", "25711", date(2021, 8, 1), date(2021, 8, 1), None, None),
            ("p1", "25916", date(2022, 8, 1), date(2022, 8, 1), None, None),
        ],
    )
    df = naar_1cho(star).sort("inschrijvingsjaar")
    assert df["verblijfsjaar_actuele_instelling"].to_list() == [1, 2]
    assert df["verblijfsjaar_actuele_opleiding_instelling"].to_list() == [1, 1]


def test_een_hoofdinschrijving_per_jaar_over_brins():
    # Hoofd op 21CY (niveau 3) en op 25LX (niveau 4) in 2022: niveau 4 wint.
    star = _star(
        [
            ("21CY", "p1", "1", 2022, date(2022, 8, 1), "25711", "MBO-3", True),
            ("25LX", "p1", "C1", 2022, date(2022, 8, 1), "25916", "MBO-4", True),
        ],
        [
            ("p1", "25711", date(2022, 8, 1), date(2022, 8, 1), None, None),
            ("p1", "25916", date(2022, 8, 1), date(2022, 8, 1), None, None),
        ],
    )
    df = naar_1cho(star)
    hoofd = df.filter(pl.col("soort_inschrijving_actuele_instelling") == LABEL_HOOFD)
    assert hoofd["opleiding_actueel_equivalent"].to_list() == ["25916"]
    neven = df.filter(pl.col("soort_inschrijving_actuele_instelling") == LABEL_NEVEN)
    assert neven.height == 1


def test_zelfde_opleiding_op_twee_brins_wordt_een_rij():
    star = _star(
        [
            ("21CY", "p1", "1", 2022, date(2022, 8, 1), "25711", "MBO-3", True),
            ("25LX", "p1", "C1", 2022, date(2022, 8, 1), "25711", "MBO-3", False),
        ],
        [("p1", "25711", date(2022, 8, 1), date(2022, 8, 1), None, None)],
    )
    assert naar_1cho(star).height == 1


def test_diploma_op_rij_van_het_diplomajaar():
    star = _star(
        [
            ("21CY", "p1", "1", 2021, date(2021, 8, 1), "25711", "MBO-3", True),
            ("21CY", "p1", "1", 2022, date(2021, 8, 1), "25711", "MBO-3", True),
        ],
        [
            (
                "p1",
                "25711",
                date(2021, 8, 1),
                date(2021, 8, 1),
                date(2023, 6, 15),
                "25711",
            )
        ],
    )
    df = naar_1cho(star).sort("inschrijvingsjaar")
    assert df["diplomajaar"].to_list() == [None, 2022]
    assert df["soort_diploma_instelling"].to_list() == [None, LABEL_DIPLOMA]


def test_diploma_na_laatste_peildatum_valt_op_laatste_rij():
    # Diploma in schooljaar 2023, maar geen rij op 1 oktober 2023.
    star = _star(
        [("21CY", "p1", "1", 2022, date(2022, 8, 1), "25711", "MBO-3", True)],
        [
            (
                "p1",
                "25711",
                date(2022, 8, 1),
                date(2022, 8, 1),
                date(2024, 2, 1),
                "25711",
            )
        ],
    )
    rij = naar_1cho(star).row(0, named=True)
    assert rij["diplomajaar"] == 2023
    assert rij["soort_diploma_instelling"] == LABEL_DIPLOMA


def test_demo_heeft_geen_dubbele_sleutels(demo_star):
    star, _ = demo_star
    df = naar_1cho(star)
    hoofd = df.filter(pl.col("soort_inschrijving_actuele_instelling") == LABEL_HOOFD)
    sleutel = hoofd.select("persoonsgebonden_nummer", "inschrijvingsjaar")
    assert sleutel.is_duplicated().sum() == 0
    rij = df.select(
        "persoonsgebonden_nummer", "inschrijvingsjaar", "opleiding_actueel_equivalent"
    )
    assert rij.is_duplicated().sum() == 0
    assert df["verblijfsjaar_actuele_instelling"].min() >= 1


def test_diploma_na_wissel_zonder_rij_valt_op_laatste_rij_van_student():
    # 1-10-2022 in 25711, in januari naar 25916, diploma juli 2023: geen rij in 25916.
    star = _star(
        [("21CY", "p1", "1", 2022, date(2022, 8, 1), "25711", "MBO-3", True)],
        [
            ("p1", "25711", date(2022, 8, 1), date(2022, 8, 1), None, None),
            (
                "p1",
                "25916",
                date(2022, 8, 1),
                date(2023, 1, 9),
                date(2023, 7, 1),
                "25916",
            ),
        ],
    )
    rij = naar_1cho(star).row(0, named=True)
    assert rij["diplomajaar"] == 2022
    assert rij["soort_diploma_instelling"] == LABEL_DIPLOMA
