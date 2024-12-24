from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from database import Base

class TickerScore(Base):
    __tablename__ = 'ticker_scores'

    ticker_symbol = Column(String, index=True, primary_key=True)
    ticker_name = Column(String, index=True)

    w_score = Column(Integer, nullable=True)
    w_squeeze = Column(Boolean, nullable=True)
    d_score = Column(Integer, nullable=True)
    d_squeeze = Column(Boolean, nullable=True)
    five_d_score = Column(Integer, nullable=True)
    five_d_squeeze = Column(Boolean, nullable=True)
    one_h_score = Column(Integer, nullable=True)
    one_h_squeeze = Column(Boolean, nullable=True)
    ninety_m_score = Column(Integer, nullable=True)
    ninety_m_squeeze = Column(Boolean, nullable=True)
    thirty_m_score = Column(Integer, nullable=True)
    thirty_m_squeeze = Column(Boolean, nullable=True)
    fifteen_m_score = Column(Integer, nullable=True)
    fifteen_m_squeeze = Column(Boolean, nullable=True)

    long_score = Column(Integer, nullable=True)
    short_score = Column(Integer, nullable=True)
    long_rank = Column(String, nullable=True)
    short_rank = Column(String, nullable=True)
    trend = Column(String, nullable=True)
    score_change_trend = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))