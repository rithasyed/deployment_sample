from pydantic import BaseModel

# Define a schema for creating an Item
class SymbolCreate(BaseModel):
    name: str

# Define a schema for returning an Item (response model)
class SymbolResponse(BaseModel):
    id: int
    name: str
    