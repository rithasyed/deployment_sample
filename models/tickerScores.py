from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from database import Base

class TickerScore(Base):
    __tablename__ = 'ticker_scores'

    id = Column(Integer, primary_key=True, index=True)
    ticker_symbol = Column(String, index=True)
    ticker_name = Column(String, index=True)

    w_score = Column(Integer, nullable=True)
    w_squeeze = Column(String, nullable=True)
    d_score = Column(Integer, nullable=True)
    d_squeeze = Column(String, nullable=True)
    five_d_score = Column(Integer, nullable=True)
    five_d_squeeze = Column(String, nullable=True)
    one_h_score = Column(Integer, nullable=True)
    one_h_squeeze = Column(String, nullable=True)
    ninety_m_score = Column(Integer, nullable=True)
    ninety_m_squeeze = Column(String, nullable=True)
    thirty_m_score = Column(Integer, nullable=True)
    thirty_m_squeeze = Column(String, nullable=True)
    fifteen_m_score = Column(Integer, nullable=True)
    fifteen_m_squeeze = Column(String, nullable=True)

    long_score = Column(Integer, nullable=True)
    short_score = Column(Integer, nullable=True)
    long_rank = Column(String, nullable=True)
    short_rank = Column(String, nullable=True)
    trend = Column(String, nullable=True)
    score_change_trend = Column(String, nullable=True)
    current_price = Column(Float, nullable=True)
    sector = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))