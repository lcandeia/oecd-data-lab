
# Países prioritários da América Latina
LATAM_COUNTRIES = {
    "BRA": "Brasil",
    "ARG": "Argentina",
    "MEX": "México",
    "CHL": "Chile",
    "COL": "Colômbia",
    "PER": "Peru",
    "URY": "Uruguai",
    "CRI": "Costa Rica",
}

# Economias para comparação internacional
REFERENCE_COUNTRIES = {
    "USA": "Estados Unidos",
    "DEU": "Alemanha",
    "JPN": "Japão",
    "GBR": "Reino Unido",
    "CAN": "Canadá",
    "TUR": "Turquia",
}

COUNTRIES = LATAM_COUNTRIES | REFERENCE_COUNTRIES

# Configurações temporais
START_PERIOD = "2014-01"
END_PERIOD = "2025-12"

# Indicador principal
INDICATOR = "CPI"

# Frequência de coleta
FREQUENCY = "M"

# Países confirmados na coleta atual
INITIAL_OECD_COUNTRIES = ["USA", "DEU"]
