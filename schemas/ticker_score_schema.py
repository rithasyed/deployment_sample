from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TickerScoreCreate(BaseModel):
    ticker_symbol: str
    ticker_name: Optional[str] = None
    interval: Optional[str] = None
    
    w_score: Optional[int] = None
    w_squeeze: Optional[str] = None
    d_score: Optional[int] = None
    d_squeeze: Optional[str] = None
    five_d_score: Optional[int] = None
    five_d_squeeze: Optional[str] = None
    one_h_score: Optional[int] = None
    one_h_squeeze: Optional[str] = None
    ninety_m_score: Optional[int] = None
    ninety_m_squeeze: Optional[str] = None
    thirty_m_score: Optional[int] = None
    thirty_m_squeeze: Optional[str] = None
    fifteen_m_score: Optional[int] = None
    fifteen_m_squeeze: Optional[str] = None
    
    long_score: Optional[int] = None
    short_score: Optional[int] = None
    long_rank: Optional[str] = None
    short_rank: Optional[str] = None
    trend: Optional[str] = None
    score_change_trend: Optional[str] = None
    current_price: Optional[float] = None
    sector: Optional[str] = None

class TickerScoreUpdate(BaseModel):

    ticker_symbol: Optional[str] = None
    ticker_name: Optional[str] = None
    interval: Optional[str] = None
    
    w_score: Optional[int] = None
    w_squeeze: Optional[str] = None
    d_score: Optional[int] = None
    d_squeeze: Optional[str] = None
    five_d_score: Optional[int] = None
    five_d_squeeze: Optional[str] = None
    one_h_score: Optional[int] = None
    one_h_squeeze: Optional[str] = None
    ninety_m_score: Optional[int] = None
    ninety_m_squeeze: Optional[str] = None
    thirty_m_score: Optional[int] = None
    thirty_m_squeeze: Optional[str] = None
    fifteen_m_score: Optional[int] = None
    fifteen_m_squeeze: Optional[str] = None
    
    long_score: Optional[int] = None
    short_score: Optional[int] = None
    long_rank: Optional[str] = None
    short_rank: Optional[str] = None
    trend: Optional[str] = None
    score_change_trend: Optional[str] = None
    current_price: Optional[float] = None
    sector: Optional[str] = None

class TickerScoreResponse(TickerScoreCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True