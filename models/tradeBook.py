from datetime import datetime, timezone
from sqlalchemy import TIMESTAMP, Column, Integer, String, Boolean, DateTime
from database import Base

# Define the 'Item' model, which represents a table in the database
class Tradebook(Base):
    __tablename__ = 'trade_book'

    id = Column(Integer, primary_key=True, index=True)
    stockname = Column(String, index=True)
    entry_price = Column(String, index=True)
    exit_price = Column(String, index=True)
    pnl = Column(String, index=True)
    status = Column(String, index=True)
    entry_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    exit_time = Column(DateTime(timezone=True), default=datetime.now(timezone.utc), nullable=True)
    stoploss = Column(String, index=True)
    target = Column(String, index=True)
    quantity = Column(String, index=True)
    capital = Column(String, index=True)
    ROI = Column(String, index=True)
    tradetype = Column(String, index=True)
    back_testing = Column(Boolean, index=True)
    interval = Column(String, index=True)
    remarks = Column(String, index=True)