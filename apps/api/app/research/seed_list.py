# apps/api/app/research/seed_list.py
"""
Curated seed list of known extreme movers (500%+ short-horizon moves).
Used to validate the scanner pipeline before running the full universe.

Sources: public news, SEC filings, WSB/Reddit archives, financial media.
Each entry includes the symbol, approximate date range, and known catalyst.
"""
from __future__ import annotations

SEED_EVENTS: list[dict] = [
    # --- Short squeezes ---
    {"symbol": "GME", "name": "GameStop", "start": "2021-01-01", "catalyst": "short_squeeze", "notes": "WSB-driven short squeeze, 140%+ SI, Melvin Capital"},
    {"symbol": "AMC", "name": "AMC Entertainment", "start": "2021-01-01", "catalyst": "short_squeeze", "notes": "Meme stock squeeze, high retail participation"},
    {"symbol": "SPRT", "name": "Support.com", "start": "2021-08-01", "catalyst": "short_squeeze", "notes": "Merger with Greenidge, high SI, low float squeeze"},
    {"symbol": "IRNT", "name": "IronNet Cybersecurity", "start": "2021-08-01", "catalyst": "short_squeeze", "notes": "De-SPAC gamma squeeze, tiny float post-merger"},
    {"symbol": "BBIG", "name": "Vinco Ventures", "start": "2021-08-01", "catalyst": "short_squeeze", "notes": "Tyde spinoff, short squeeze setup"},
    {"symbol": "ATER", "name": "Aterian", "start": "2021-08-01", "catalyst": "short_squeeze", "notes": "Low float, high SI squeeze"},
    {"symbol": "BGFV", "name": "Big 5 Sporting", "start": "2021-10-01", "catalyst": "short_squeeze", "notes": "Special dividend + short squeeze"},
    {"symbol": "ISPC", "name": "iSpecimen", "start": "2021-11-01", "catalyst": "short_squeeze", "notes": "Low float squeeze, COVID testing demand"},

    # --- SPAC / De-SPAC pops ---
    {"symbol": "DWAC", "name": "Digital World Acquisition (Trump Media)", "start": "2021-10-01", "catalyst": "spac_despac", "notes": "Trump Media SPAC announcement, political meme trade"},
    {"symbol": "BKKT", "name": "Bakkt Holdings", "start": "2021-10-01", "catalyst": "spac_despac", "notes": "De-SPAC pop, Mastercard partnership rumors"},
    {"symbol": "PHUN", "name": "Phunware", "start": "2021-10-01", "catalyst": "spac_despac", "notes": "Trump-adjacent tech, sympathy move with DWAC"},
    {"symbol": "ESSC", "name": "East Side Games", "start": "2021-12-01", "catalyst": "spac_despac", "notes": "De-SPAC with tiny float, gamma squeeze"},
    {"symbol": "ALLG", "name": "Allego", "start": "2022-03-01", "catalyst": "spac_despac", "notes": "EV charging de-SPAC, low float"},

    # --- Biotech catalysts ---
    {"symbol": "SAVA", "name": "Cassava Sciences", "start": "2021-01-01", "catalyst": "biotech_catalyst", "notes": "Alzheimer's drug data, simufilam"},
    {"symbol": "MRNA", "name": "Moderna", "start": "2020-03-01", "catalyst": "biotech_catalyst", "notes": "COVID vaccine development"},
    {"symbol": "NVAX", "name": "Novavax", "start": "2020-03-01", "catalyst": "biotech_catalyst", "notes": "COVID vaccine candidate"},
    {"symbol": "AGTC", "name": "Applied Genetic Tech", "start": "2021-01-01", "catalyst": "biotech_catalyst", "notes": "Gene therapy data readout"},
    {"symbol": "OCGN", "name": "Ocugen", "start": "2021-02-01", "catalyst": "biotech_catalyst", "notes": "Covaxin partnership with Bharat Biotech"},

    # --- Penny stock / low float pumps ---
    {"symbol": "CEI", "name": "Camber Energy", "start": "2021-09-01", "catalyst": "penny_stock_pump", "notes": "Sub-$1 energy stock, social media pump"},
    {"symbol": "MULN", "name": "Mullen Automotive", "start": "2022-03-01", "catalyst": "penny_stock_pump", "notes": "EV penny stock, retail pump, dilution history"},
    {"symbol": "FFIE", "name": "Faraday Future", "start": "2024-05-01", "catalyst": "penny_stock_pump", "notes": "EV penny stock, meme-driven squeeze from sub-$0.10"},
    {"symbol": "TOP", "name": "TOP Financial Group", "start": "2024-01-01", "catalyst": "penny_stock_pump", "notes": "Hong Kong fintech micro-cap, extreme low float"},
    {"symbol": "MEGL", "name": "Magic Empire Global", "start": "2022-08-01", "catalyst": "penny_stock_pump", "notes": "IPO day 2800%+ move, ~1M share float"},
    {"symbol": "HCDI", "name": "Harbor Custom Dev", "start": "2022-08-01", "catalyst": "penny_stock_pump", "notes": "Micro-cap homebuilder, low float squeeze"},
    {"symbol": "AMTD", "name": "AMTD Digital", "start": "2022-07-01", "catalyst": "penny_stock_pump", "notes": "HKD parent, mysterious 32000% rally post-IPO"},

    # --- HKD (historic outlier) ---
    {"symbol": "HKD", "name": "AMTD Digital", "start": "2022-07-01", "catalyst": "penny_stock_pump", "notes": "IPO $7.80 to $2,555, no clear catalyst, SEC scrutiny"},

    # --- Restructuring / bankruptcy exit ---
    {"symbol": "HERTZ", "name": "Hertz (OTC)", "start": "2020-06-01", "catalyst": "restructuring", "notes": "Bankruptcy rally driven by retail, Robinhood traders"},
    {"symbol": "CURO", "name": "CURO Group", "start": "2023-01-01", "catalyst": "restructuring", "notes": "Lending company restructuring"},

    # --- Merger / acquisition ---
    {"symbol": "TWTR", "name": "Twitter", "start": "2022-04-01", "catalyst": "merger_acquisition", "notes": "Elon Musk takeover bid"},

    # --- Recent 2023-2024 extreme movers ---
    {"symbol": "SMCI", "name": "Super Micro Computer", "start": "2023-01-01", "catalyst": "earnings_surprise", "notes": "AI server demand, repeated earnings beats"},
    {"symbol": "DJT", "name": "Trump Media & Technology", "start": "2024-03-01", "catalyst": "spac_despac", "notes": "DWAC→DJT merger completion, political meme stock"},
    {"symbol": "LUNR", "name": "Intuitive Machines", "start": "2024-02-01", "catalyst": "sector_momentum", "notes": "Moon landing mission, space sector momentum"},
    {"symbol": "RDDT", "name": "Reddit", "start": "2024-03-01", "catalyst": "sector_momentum", "notes": "IPO pop, social media / AI data licensing hype"},
    {"symbol": "MGOL", "name": "MGO Global", "start": "2023-08-01", "catalyst": "penny_stock_pump", "notes": "Micro-cap, extreme low float IPO"},
    {"symbol": "PRST", "name": "Presto Automation", "start": "2023-09-01", "catalyst": "penny_stock_pump", "notes": "AI restaurant tech, low float squeeze"},
]


def get_seed_symbols() -> list[str]:
    """Return just the ticker symbols from the seed list."""
    return sorted(set(e["symbol"] for e in SEED_EVENTS))


def get_seed_events_by_catalyst(catalyst: str) -> list[dict]:
    """Filter seed events by catalyst type."""
    return [e for e in SEED_EVENTS if e["catalyst"] == catalyst]


def get_seed_catalysts() -> list[str]:
    """Return all unique catalyst types in the seed list."""
    return sorted(set(e["catalyst"] for e in SEED_EVENTS))
