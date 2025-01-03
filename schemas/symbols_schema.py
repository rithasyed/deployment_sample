from pydantic import BaseModel

class SymbolBase(BaseModel):
    name: str
# Define a schema for creating an Item
class SymbolCreate(SymbolBase):
    full_name: str
    category_id: int
    
# Define a schema for returning an Item (response model)
class SymbolResponse(BaseModel):
    id: int
    name: str
    full_name: str
    category_id: int

class Symbol(SymbolBase):
    id: int
    name: str
    full_name: str
    category_id: int

    class Config:
        from_attributes = True
    