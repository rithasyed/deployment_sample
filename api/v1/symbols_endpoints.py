from sqlalchemy.orm import Session
from fastapi import  APIRouter, Depends, HTTPException
from schemas import symbols_schema
from services import symbol_crud
from database import get_db

router = APIRouter()

@router.get("/symbols/file")
def write_symbol_names_to_file(db: Session = Depends(get_db)):

    # Fetch all item names
    symbol_names = symbol_crud.get_symbols(db)
    symbols = [symbol.name for symbol in symbol_names]
    # Define the file path for symbols.txt
    file_path = "symbols.txt"
    
    # Write the item names to the file (overwriting if it exists)
    with open(file_path, "w") as file:
        for name in symbols:
            file.write(f"{name}\n")
    
    return {"message": f"Item names written to {file_path}"}

# Endpoint to create a new symbol
@router.post("/symbols", response_model=symbols_schema.SymbolCreate)
def create_symbol(symbol: symbols_schema.SymbolCreate, db: Session = Depends(get_db)):
    return symbol_crud.create_symbol(db, symbol)

# Endpoint to retrieve a specific symbol by its ID
@router.get("/symbols/{symbol_id}", response_model=symbols_schema.SymbolResponse)
def read_symbol(symbol_id: int, db: Session = Depends(get_db)):
    
    db_symbol = symbol_crud.get_symbol(db, symbol_id)
    if db_symbol is None:
        raise HTTPException(status_code=404, detail="symbol not found")
    return db_symbol

# Endpoint to retrieve all symbols
@router.get("/symbols/", response_model=list[symbols_schema.SymbolResponse])
def read_symbols(db: Session = Depends(get_db)):
    return symbol_crud.get_symbols(db)
