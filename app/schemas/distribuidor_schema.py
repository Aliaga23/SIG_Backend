from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from enum import Enum

class EstadoDistribuidor(str, Enum):
    disponible = "disponible"
    ocupado = "ocupado"
    inactivo = "inactivo"

class DistribuidorBase(BaseModel):
    nombre: str
    apellido: str
    carnet: str
    telefono: str
    email: EmailStr
    licencia: str
    latitud: Optional[float] = Field(default=None)
    longitud: Optional[float] = Field(default=None)

class DistribuidorCreate(DistribuidorBase):
    password: str  

class DistribuidorUpdate(DistribuidorBase):
    password: str  

class DistribuidorOut(DistribuidorBase):
    id: UUID
    activo: bool
    estado: EstadoDistribuidor

    class Config:
        from_attributes = True

class CambiarEstadoRequest(BaseModel):
    estado: EstadoDistribuidor
