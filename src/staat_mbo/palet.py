"""Npuls-kleuren en grafiekpaletten (bron: vormgever-npuls-huisstijl, design-tokens.json).

Alleen waarden uit de tokens; geen streamlit-afhankelijkheid, zodat ook de
definities er gebruik van kunnen maken.
"""

BLAUW = "#3D68EC"
ORANJE = "#DD784B"
GROEN = "#00AF81"
GEEL = "#F4D74B"
ROZE = "#F4D9DC"
ZWART = "#000000"
WIT = "#FFFFFF"
LICHT_BLAUW = "#D6E2FD"
LICHT_GROEN = "#CCEEE6"
LICHT_ROZE = "#FAEAEA"
LICHT_ORANJE = "#FFE4D8"
LICHT_GEEL = "#FCF5D4"
GRIJS_200 = "#DCDCE0"
GRIJS_400 = "#9A9AA2"
GRIJS_600 = "#5C5C66"

## data_visualization.categorical_order
CATEGORISCH = [BLAUW, ORANJE, GROEN, GEEL, ROZE, ZWART]
## data_visualization.sequential
SEQUENTIEEL = [LICHT_BLAUW, BLAUW]
## Vaste kleur per niveau (1 t/m 4) en per herkomst: de eerste vier categorische.
NIVEAUKLEUREN = CATEGORISCH[:4]
HERKOMSTKLEUREN = CATEGORISCH[:4]
## Neutraal grijs voor "nog niet waarneembaar": geen uitkomst, dus geen kleur.
NEUTRAAL = GRIJS_200

## Loopbaancategorieën: diploma's blauw/groen, zonder diploma warm, uitval grijs.
## Geen rood: het is geen oordeel.
CATEGORIE_KLEUREN = [
    BLAUW,
    LICHT_BLAUW,
    LICHT_GROEN,
    GEEL,
    ORANJE,
    LICHT_ORANJE,
    ROZE,
    GRIJS_600,
    GRIJS_200,
]

FONT = "'Plus Jakarta Sans', 'General Sans', system-ui, sans-serif"

## Streamlit-thema; ``smbo dashboard`` geeft het als ``--theme.*`` mee, zodat het
## ook geldt als de app vanuit een andere map start (.streamlit/config.toml van
## de werkmap wordt dan niet gelezen). Houd .streamlit/config.toml hiermee gelijk.
THEMA = {
    "base": "light",
    "primaryColor": BLAUW,
    "backgroundColor": WIT,
    "secondaryBackgroundColor": LICHT_BLAUW,
    "textColor": ZWART,
    "baseRadius": "large",
    "sidebar.backgroundColor": ROZE,
    "sidebar.secondaryBackgroundColor": WIT,
    "sidebar.textColor": ZWART,
    "sidebar.primaryColor": BLAUW,
}


def thema_opties() -> list[str]:
    """Het thema als opdrachtregelopties voor ``streamlit run``."""
    return [x for k, v in THEMA.items() for x in (f"--theme.{k}", v)]
