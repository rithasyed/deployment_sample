from sqlalchemy.orm import Session
from models.symbols import Symbols
from schemas.symbols_schema import SymbolCreate, Symbol

# Create a new symbol in the database
def create_symbol(db: Session, symbol: SymbolCreate):
    db_symbol = Symbols(
        name=symbol.name,
        full_name=symbol.full_name,
        category_id=symbol.category_id
    )
    db.add(db_symbol)
    db.commit()
    db.refresh(db_symbol)
    return Symbol(
        id=db_symbol.id,
        name=db_symbol.name,
        full_name=db_symbol.full_name,
        category_id=db_symbol.category_id
    )

# Retrieve a single symbol by its ID
def get_symbol(db: Session, symbol_id: int):
    return db.query(Symbols).filter(Symbols.id == symbol_id).first()

# Retrieve all symbols
def get_symbols(db: Session):
    return db.query(Symbols).all()

def get_symbol_names(db: Session):
    # Query to fetch only the names of items
    return [symbol for symbol in db.query(Symbols.name).all()]

