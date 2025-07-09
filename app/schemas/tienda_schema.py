from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID

class TiendaBase(BaseModel):
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    email: Optional[str] = None
    latitud: float
    longitud: float
    descripcion: Optional[str] = None

class TiendaCreate(TiendaBase):
    pass

class TiendaUpdate(TiendaBase):
    nombre: Optional[str] = None
    direccion: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class TiendaResponse(TiendaBase):
    id: UUID

    class Config:
        from_attributes = True
