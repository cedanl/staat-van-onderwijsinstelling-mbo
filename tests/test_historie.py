from staat_mbo.historie import Melding, meldingen
from tests.maak import waarneming


def _teksten(w, begin):
    return [m.tekst for m in meldingen(w) if m.tekst.startswith(begin)]


def test_demodata_van_zes_jaar_geeft_dr_sr_en_rendementsmelding():
    w = waarneming(2020, 2025)
    assert _teksten(w, "Jaarresultaat") == []
    (dr,) = _teksten(w, "Diplomaresultaat")
    assert "diploma's van vóór 01-08-2020" in dr
    assert "2022 t/m 2024" in dr
    (sr,) = _teksten(w, "Startersresultaat")
    assert "4 jaar terug in plaats van 6" in sr
    assert len(_teksten(w, "Rendement")) == 1


def test_te_weinig_oktobers_voor_een_driejaarscijfer():
    w = waarneming(2022, 2024)
    (jr,) = _teksten(w, "Jaarresultaat")
    assert "minstens 4 nodig" in jr and "3 aaneengesloten" in jr
    assert "nog geen driejaarscijfer" in _teksten(w, "Startersresultaat")[0]
    assert "nog geen driejaarscijfer" in _teksten(w, "Diplomaresultaat")[0]


def test_genoeg_historie_geeft_geen_dr_en_sr_melding():
    w = waarneming(2016, 2025)
    assert _teksten(w, "Diplomaresultaat") == []
    assert _teksten(w, "Startersresultaat") == []
    assert _teksten(w, "Jaarresultaat") == []


def test_gat_wordt_genoemd_met_de_jaren_zonder_cijfer():
    w = waarneming(2018, 2025, gaten=[2022])
    (gat,) = _teksten(w, "Door het gat")
    assert "2022" in gat
    assert "2021-2022" in gat and "2022-2023" in gat
    assert "2020-2021" not in gat


def test_gat_buiten_de_waarneming_geeft_geen_melding():
    assert _teksten(waarneming(2020, 2025, gaten=[2018]), "Door het gat") == []


def test_ernst_is_info_of_waarschuwing():
    assert {m.ernst for m in meldingen(waarneming(2022, 2024))} <= {
        "info",
        "waarschuwing",
    }
    assert all(isinstance(m, Melding) for m in meldingen(waarneming(2020, 2025)))


def test_rendementsmelding_zonder_zes_aaneengesloten_oktobers():
    (tekst,) = _teksten(waarneming(2022, 2025), "Rendement")
    assert "nog niet te zien" in tekst


DR_ZIN = (
    "Diplomaresultaat: diploma's van vóór 01-08-2020 zitten niet in je "
    "bestanden. Voor de driejaarscijfers met laatste jaartijdvak 2022 t/m "
    "2024 ontbreken diploma's uit de 5 jaar terug; daar is het cijfer een "
    "ondergrens. Upload oudere RO's voor een volledig cijfer."
)
SR_ZIN = (
    "Startersresultaat: we kijken 4 jaar terug in plaats van 6. Wie 5-6 "
    "jaar geleden al eens bij je stond en terugkomt, telt als nieuwe student."
)
RENDEMENT_ZIN = "Rendement nominaal + 1 voor niveau 4 is pas te zien vanaf cohort 2020."
JR_ZIN = (
    "Jaarresultaat: nog geen driejaarscijfer. Je hebt 3 aaneengesloten "
    "1 oktobers, er zijn er minstens 4 nodig."
)


def test_exacte_zinnen_zijn_vastgelegd():
    assert [(m.ernst, m.tekst) for m in meldingen(waarneming(2020, 2025))] == [
        ("waarschuwing", DR_ZIN),
        ("waarschuwing", SR_ZIN),
        ("info", RENDEMENT_ZIN),
    ]
    assert meldingen(waarneming(2022, 2024))[0].tekst == JR_ZIN
