"""
Configuration constants and event catalog for the Fintech Screener.
"""

# Market Assets
TICKERS = ['^MERV', 'YPF', 'GGAL', 'GGAL.BA', 'ARS=X']

# Digital Signal Processing Defaults
DSP_WINDOW_LENGTH = 31
DSP_POLYORDER = 3

# Historical Events Catalog for Anomaly Context
EVENT_CATALOG = [
    {"date": "2023-04-25", "title": "Blue Dollar historic surge past 400 ARS", "category": "Market/External"},
    {"date": "2023-06-24", "title": "Sergio Massa announced as UP candidate", "category": "Political/Rumor"},
    {"date": "2023-08-14", "title": "PASO Elections Shock: Milei wins, 22% Devaluation", "category": "Official Measure"},
    {"date": "2023-10-23", "title": "General Elections: Massa vs Milei run-off", "category": "Political/Rumor"},
    {"date": "2023-11-20", "title": "Javier Milei wins Presidential Run-off", "category": "Political/Rumor"},
    {"date": "2023-12-10", "title": "Presidential Inauguration of Javier Milei", "category": "Official Measure"},
    {"date": "2023-12-13", "title": "Caputo Announces 54% Devaluation", "category": "Official Measure"},
    {"date": "2023-12-20", "title": "Mega DNU 70/2023 Deregulation Announced", "category": "Official Measure"},
    {"date": "2024-01-24", "title": "First General Strike (CGT)", "category": "Protest/Strike"},
    {"date": "2024-02-06", "title": "First Ley Ómnibus debate collapses", "category": "Political/Rumor"},
    {"date": "2024-04-23", "title": "Massive Public University March", "category": "Protest/Strike"},
    {"date": "2024-05-14", "title": "Inflation officially drops to single digits", "category": "Official Measure"},
    {"date": "2024-06-13", "title": "Ley Bases approved in Senate amid protests", "category": "Official Measure"},
    {"date": "2024-06-28", "title": "Ley Bases definitively approved in Deputies", "category": "Official Measure"},
    {"date": "2024-07-13", "title": "Phase 2 of Economic Plan announced", "category": "Official Measure"},
    {"date": "2024-08-05", "title": "Global Market Sell-off (Black Monday)", "category": "Market/External"},
    {"date": "2024-10-02", "title": "Second Massive University March", "category": "Protest/Strike"},
    {"date": "2024-11-13", "title": "Argentine Country Risk drops below 800 pts", "category": "Market/External"},
    {"date": "2025-01-20", "title": "Inauguration of US President Trump", "category": "Market/External"},
    {"date": "2025-03-01", "title": "Opening of Regular Congressional Sessions", "category": "Official Measure"}
]
