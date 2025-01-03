from sqlalchemy import Column, Integer, String 
from database import Base

class TickerCategory(Base):
    __tablename__ = 'ticker_categories'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)