from sqlalchemy import Column, Integer, String
from database import Base
# Define the 'Item' model, which represents a table in the database
class Symbols(Base):
    __tablename__ = 'symbols'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)