from pydantic import BaseModel
from uuid import UUID

class ProductoBase(BaseModel):
    nombre: str
    descripcion: str | None = None
    precio: float
    talla: str | None = None
    color: str | None = None
    stock: int

class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(ProductoBase):
    pass

class ProductoOut(ProductoBase):
    id: UUID

    class Config:
        from_attributes = True
