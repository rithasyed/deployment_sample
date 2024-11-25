from pydantic import BaseModel
from typing import Optional

# Schema for creating a new trade (with optional fields)
class TradebookCreate(BaseModel):
    stockname: str
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: Optional[str] = None
    entry_time: Optional[str] = None
    exit_time: Optional[str] = None
    tradetype: Optional[str] = None


# Schema for updating an existing trade
class TradebookUpdate(BaseModel):
    stockname: Optional[str] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    pnl: Optional[float] = None
    status: Optional[str] = None
    entry_time: Optional[str] = None
    exit_time: Optional[str] = None
    tradetype: Optional[str] = None

class backTestCreate(BaseModel):
    stockname: str
    interval: str