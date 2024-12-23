from pydantic import BaseModel

class SymbolBase(BaseModel):
    name: str
# Define a schema for creating an Item
class SymbolCreate(SymbolBase):
    pass

# Define a schema for returning an Item (response model)
class SymbolResponse(BaseModel):
    id: int
    name: str

class Symbol(SymbolBase):
    id: int
    name: str
    class Config:
        from_attributes = True
    