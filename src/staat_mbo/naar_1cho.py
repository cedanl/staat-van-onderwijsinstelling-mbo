"""Star van mbo-bekostiging-bestanden → 1CHO-vorm voor staat1cho.

Eén functie per vertaalregel; ``naar_1cho`` zet ze achter elkaar. De regels
komen uit het haalbaarheidsonderzoek (cedanl/mbo-bekostiging-bestanden#389).
"""

from pathlib import Path

import polars as pl

KOLOMMEN_1CHO = [
    "persoonsgebonden_nummer",
    "soort_hoger_onderwijs",
    "soort_inschrijving_actuele_instelling",
    "verblijfsjaar_actuele_instelling",
    "verblijfsjaar_actuele_opleiding_instelling",
    "inschrijvingsjaar",
    "diplomajaar",
    "soort_diploma_instelling",
    "geslacht",
    "opleidingsvorm",
    "indicatie_internationale_student",
    "indicatie_eer_actueel",
    "croho_onderdeel_actuele_opleiding",
    "vestigingsnummer_gemeentenaam_volgens_rio",
    "opleiding_actueel_equivalent",
    "opleidingscode_naam_opleiding",
    "type_hoger_onderwijs_binnen_soort_hoger_onderwijs",
    "leeftijd_per_peildatum_1_oktober",
    "postcodecijfers_student_op_1_oktober",
    "postcodecijfers_van_de_hoogste_vooropl_voor_het_ho",
    "nominale_duur",
]
## Minimaal aantal inschrijvingen per opleiding × leerweg voor een eigen
## nominale duur; daaronder geldt de standaardduur per niveau.
MIN_INSCHRIJVINGEN_DUUR = 10
## Niveau 4 is meestal 4 jaar (studielast 6400 SBU in RIO), soms 3.
STANDAARDDUUR = {1: 1, 2: 2, 3: 3, 4: 4}
SOORT_ONDERWIJS = "mbo"
LABEL_HOOFD = "hoofdinschrijving binnen het domein actuele instelling"
LABEL_NEVEN = "neveninschrijving binnen het domein actuele instelling"
LABEL_DIPLOMA = "Diploma mbo binnen de actuele instelling"
_GESLACHT = {"M": "man", "V": "vrouw"}
_P = "_persoon_id"


def eerste_peiljaar(datum: pl.Expr) -> pl.Expr:
    """Schooljaar van de eerste 1 oktober op of na ``datum``."""
    jaar = datum.dt.year()
    return pl.when(datum <= pl.date(jaar, 10, 1)).then(jaar).otherwise(jaar + 1)


def diplomajaar(datum: pl.Expr) -> pl.Expr:
    """Schooljaar (oktober–september) waarin ``datum`` valt."""
    jaar = datum.dt.year()
    return pl.when(datum.dt.month() >= 10).then(jaar).otherwise(jaar - 1)


def leeftijd_op_1_oktober(geboortedatum: pl.Expr, jaar: pl.Expr) -> pl.Expr:
    na_peildatum = (geboortedatum.dt.month() > 10) | (
        (geboortedatum.dt.month() == 10) & (geboortedatum.dt.day() > 1)
    )
    return jaar - geboortedatum.dt.year() - na_peildatum.cast(pl.Int32)


def _niveau_getal(niveau: pl.Expr) -> pl.Expr:
    return niveau.str.extract(r"(\d)").cast(pl.Int32)


def _kies_rij_per_opleiding(sj: pl.DataFrame) -> pl.DataFrame:
    """Eén rij per persoon × schooljaar × opleiding; hoofdinschrijving wint."""
    return sj.sort(
        [_P, "Schooljaar", "Opleidingcode", "_hoofdinschrijving", "DatumBegin"],
        descending=[False, False, False, True, True],
        nulls_last=True,
    ).unique([_P, "Schooljaar", "Opleidingcode"], keep="first", maintain_order=True)


def _markeer_hoofdinschrijving(df: pl.DataFrame) -> pl.DataFrame:
    """Per persoon × schooljaar over het hele bestuur één hoofdinschrijving.

    Hoogste niveau, dan laagste crebo, dan recentste start; gekozen uit de
    hoofdinschrijvingen per BRIN.
    """
    volgorde = df.with_columns(_niveau=_niveau_getal(pl.col("Niveau"))).sort(
        [
            _P,
            "Schooljaar",
            "_hoofdinschrijving",
            "_niveau",
            "Opleidingcode",
            "DatumBegin",
        ],
        descending=[False, False, True, True, False, True],
        nulls_last=True,
    )
    eerste = pl.int_range(pl.len()).over([_P, "Schooljaar"]) == 0
    return volgorde.with_columns(
        _hoofd=eerste & pl.col("_hoofdinschrijving").fill_null(False)
    ).drop("_niveau")


def _starts(star: dict[str, pl.DataFrame]) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Eerste peiljaar per persoon en per persoon × opleiding.

    De RO levert de startdatum mee, ook van vóór de gekozen periode; de
    schooljaar-feiten vullen aan waar die ontbreekt (TBG-i).
    """
    ins = star["fact_inschrijving"]
    sj = star["fact_inschrijving_schooljaar"]
    datums = pl.concat(
        [
            ins.select(
                _P,
                "Opleidingcode",
                pl.col("DatumInschrijving").alias("_instelling"),
                pl.col("DatumBegin").alias("_opleiding"),
            ),
            sj.select(
                _P,
                "Opleidingcode",
                pl.col("DatumBegin").alias("_instelling"),
                pl.col("DatumBegin").alias("_opleiding"),
            ),
        ],
        how="vertical_relaxed",
    )
    persoon = datums.group_by(_P).agg(
        _start_instelling=eerste_peiljaar(pl.col("_instelling")).min()
    )
    opleiding = datums.group_by(_P, "Opleidingcode").agg(
        _start_opleiding=eerste_peiljaar(pl.col("_opleiding")).min()
    )
    return persoon, opleiding


def _diplomas(df: pl.DataFrame, ins: pl.DataFrame) -> pl.DataFrame:
    """Zet diplomajaar op de rij van die opleiding in of vóór het diplomajaar.

    Is er geen rij in of vóór het diplomajaar, dan de vroegste rij van die
    opleiding. Heeft de opleiding geen rij op 1 oktober (bijv. gewisseld na
    1 oktober), dan de laatste rij van de student in of vóór het diplomajaar,
    bij voorkeur de hoofdinschrijving; anders telt het diploma niet mee en
    lijkt de student uitgevallen.
    """
    dip = (
        ins.filter(pl.col("DIP_DatumResultaat").is_not_null())
        .select(
            _P,
            pl.col("DIP_Opleidingcode").alias("Opleidingcode"),
            diplomajaar(pl.col("DIP_DatumResultaat")).alias("_diplomajaar"),
        )
        .group_by(_P, "Opleidingcode")
        .agg(pl.col("_diplomajaar").min())
    )
    rijen = df.select(_P, "Opleidingcode", "Schooljaar", "_hoofd")
    eigen = (
        rijen.join(dip, on=[_P, "Opleidingcode"])
        .group_by(_P, "Opleidingcode", "_diplomajaar")
        .agg(
            pl.col("Schooljaar")
            .filter(pl.col("Schooljaar") <= pl.col("_diplomajaar"))
            .max()
            .alias("_voor"),
            pl.col("Schooljaar").min().alias("_eerste"),
        )
        .select(
            _P,
            "Opleidingcode",
            "_diplomajaar",
            pl.coalesce("_voor", "_eerste").alias("Schooljaar"),
        )
    )
    zonder_rij = dip.join(rijen, on=[_P, "Opleidingcode"], how="anti")
    ander = (
        rijen.join(zonder_rij.select(_P, "_diplomajaar"), on=_P)
        .filter(pl.col("Schooljaar") <= pl.col("_diplomajaar"))
        .sort([_P, "Schooljaar", "_hoofd"], descending=[False, True, True])
        .unique([_P, "_diplomajaar"], keep="first", maintain_order=True)
        .select(_P, "Opleidingcode", "_diplomajaar", "Schooljaar")
    )
    doel = (
        pl.concat([eigen, ander], how="vertical_relaxed")
        .group_by(_P, "Opleidingcode", "Schooljaar")
        .agg(pl.col("_diplomajaar").min())
    )
    return df.join(doel, on=[_P, "Opleidingcode", "Schooljaar"], how="left")


def nominale_duur(star: dict[str, pl.DataFrame]) -> pl.DataFrame:
    """Nominale duur in jaren per opleiding × leerweg, uit de geplande einddatum.

    De school kan de geplande einddatum van één student verschuiven bij
    vertraging; daarom de meest voorkomende geplande duur over alle
    inschrijvingen, niet die van de student zelf. De datum hoort bij de
    inschrijving: inschrijvingen met meer dan één opleiding tellen niet mee.
    Bij een gelijke stand de langste duur, zodat niemand onterecht te laat is.
    """
    sleutel = [_P, "BRIN", "Inschrijvingvolgnummer"]
    ins = star["fact_inschrijving"].unique([*sleutel, "Opleidingcode"])
    een_opleiding = ins.filter(pl.col("Opleidingcode").n_unique().over(sleutel) == 1)
    dagen = (
        pl.col("DatumUitschrijvingGepland") - pl.col("DatumInschrijving")
    ).dt.total_days() + 1
    jaren = een_opleiding.drop_nulls(
        ["DatumInschrijving", "DatumUitschrijvingGepland"]
    ).select(
        "Opleidingcode",
        "Leertraject",
        (dagen / 365.25).round().clip(lower_bound=1).cast(pl.Int32).alias("_jaren"),
    )
    return (
        jaren.group_by("Opleidingcode", "Leertraject", "_jaren")
        .len()
        .with_columns(
            pl.col("len").sum().over("Opleidingcode", "Leertraject").alias("_n")
        )
        .filter(pl.col("_n") >= MIN_INSCHRIJVINGEN_DUUR)
        .sort(["len", "_jaren"], descending=True)
        .unique(["Opleidingcode", "Leertraject"], keep="first", maintain_order=True)
        .select("Opleidingcode", "Leertraject", pl.col("_jaren").alias("nominale_duur"))
        .sort("Opleidingcode", "Leertraject")
    )


def opleidingen_met_standaardduur(
    df: pl.DataFrame, duur: pl.DataFrame
) -> tuple[int, int]:
    """(zonder eigen nominale duur, totaal) over opleiding × leerweg in de uitvoer."""
    opleidingen = df.select(
        pl.col("opleiding_actueel_equivalent").alias("Opleidingcode"),
        pl.col("opleidingsvorm").alias("Leertraject"),
    ).unique()
    zonder = opleidingen.join(duur, on=["Opleidingcode", "Leertraject"], how="anti")
    return zonder.height, opleidingen.height


def naar_1cho(
    star: dict[str, pl.DataFrame], duur: pl.DataFrame | None = None
) -> pl.DataFrame:
    """Zet de star om naar één rij per student × inschrijvingsjaar × opleiding.

    ``duur`` komt uit [nominale_duur]; zonder tabel, of voor een opleiding die
    er niet in staat, geldt de standaardduur per niveau.
    """
    if duur is None:
        duur = pl.DataFrame(
            schema={
                "Opleidingcode": pl.Utf8,
                "Leertraject": pl.Utf8,
                "nominale_duur": pl.Int32,
            }
        )
    df = _markeer_hoofdinschrijving(
        _kies_rij_per_opleiding(star["fact_inschrijving_schooljaar"])
    )
    persoon, opleiding = _starts(star)
    opleidingen = star["dim_opleiding"].select(
        "Opleidingcode", "Opleiding_naam", "Opleiding_domein"
    )
    instellingen = star["dim_instelling"].select("BRIN", "Instelling_naam")
    df = (
        df.join(persoon, on=_P, how="left")
        .join(opleiding, on=[_P, "Opleidingcode"], how="left")
        .join(
            star["dim_deelnemer"].select(_P, "Geboortedatum", "Geslacht"),
            on=_P,
            how="left",
        )
        .join(opleidingen.unique("Opleidingcode"), on="Opleidingcode", how="left")
        .join(instellingen.unique("BRIN"), on="BRIN", how="left")
        .join(duur, on=["Opleidingcode", "Leertraject"], how="left")
    )
    df = _diplomas(df, star["fact_inschrijving"])
    leeg = pl.lit(None, dtype=pl.Utf8)
    return df.select(
        pl.col(_P).alias("persoonsgebonden_nummer"),
        pl.lit(SOORT_ONDERWIJS).alias("soort_hoger_onderwijs"),
        pl.when(pl.col("_hoofd"))
        .then(pl.lit(LABEL_HOOFD))
        .otherwise(pl.lit(LABEL_NEVEN))
        .alias("soort_inschrijving_actuele_instelling"),
        (pl.col("Schooljaar") - pl.col("_start_instelling") + 1)
        .clip(lower_bound=1)
        .cast(pl.Int32)
        .alias("verblijfsjaar_actuele_instelling"),
        (pl.col("Schooljaar") - pl.col("_start_opleiding") + 1)
        .clip(lower_bound=1)
        .cast(pl.Int32)
        .alias("verblijfsjaar_actuele_opleiding_instelling"),
        pl.col("Schooljaar").cast(pl.Int32).alias("inschrijvingsjaar"),
        pl.col("_diplomajaar").cast(pl.Int32).alias("diplomajaar"),
        pl.when(pl.col("_diplomajaar").is_not_null())
        .then(pl.lit(LABEL_DIPLOMA))
        .otherwise(leeg)
        .alias("soort_diploma_instelling"),
        pl.col("Geslacht")
        .replace_strict(_GESLACHT, default=None, return_dtype=pl.Utf8)
        .alias("geslacht"),
        pl.col("Leertraject").alias("opleidingsvorm"),
        leeg.alias("indicatie_internationale_student"),
        leeg.alias("indicatie_eer_actueel"),
        pl.col("Opleiding_domein").alias("croho_onderdeel_actuele_opleiding"),
        pl.concat_str(
            "BRIN", "Instelling_naam", separator=" ", ignore_nulls=True
        ).alias("vestigingsnummer_gemeentenaam_volgens_rio"),
        pl.col("Opleidingcode").alias("opleiding_actueel_equivalent"),
        pl.col("Opleiding_naam").alias("opleidingscode_naam_opleiding"),
        pl.concat_str(pl.lit("niveau "), _niveau_getal(pl.col("Niveau"))).alias(
            "type_hoger_onderwijs_binnen_soort_hoger_onderwijs"
        ),
        leeftijd_op_1_oktober(pl.col("Geboortedatum"), pl.col("Schooljaar"))
        .cast(pl.Int32)
        .alias("leeftijd_per_peildatum_1_oktober"),
        leeg.alias("postcodecijfers_student_op_1_oktober"),
        leeg.alias("postcodecijfers_van_de_hoogste_vooropl_voor_het_ho"),
        pl.coalesce(
            "nominale_duur",
            _niveau_getal(pl.col("Niveau")).replace_strict(
                STANDAARDDUUR, default=None, return_dtype=pl.Int32
            ),
        )
        .cast(pl.Int32)
        .alias("nominale_duur"),
    ).sort(
        "persoonsgebonden_nummer", "inschrijvingsjaar", "opleiding_actueel_equivalent"
    )


def schrijf_1cho(df: pl.DataFrame, pad: Path) -> None:
    """Schrijf in het formaat dat ``staat1cho::maak_basisbestand`` leest."""
    pad.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(pad, separator=";", null_value="")
