from typing import List
from models.ticker_categories import TickerCategory
from sqlalchemy.orm import Session

def get_ticker_categories(db: Session) -> List[TickerCategory]:
    """
    Retrieve all ticker categories from the database.
    """
    return db.query(TickerCategory).all()