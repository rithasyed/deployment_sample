from requests import Session
from models.ticker_categories import TickerCategory


def seed_categories(db: Session):
    categories = [
        {"name": "Stocks", "description": "Individual company stocks"},
        {"name": "Indices", "description": "Market indices and their ETFs"},
        {"name": "Sectors", "description": "Sector-specific ETFs"},
        {"name": "Futures", "description": "Futures contracts"},
        {"name": "Crypto", "description": "Cryptocurrency-related instruments"}
    ]
    
    for category in categories:
        existing = db.query(TickerCategory).filter(TickerCategory.name == category["name"]).first()
        if not existing:
            db_category = TickerCategory(**category)
            db.add(db_category)
    
    db.commit()