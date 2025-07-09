from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional

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

    class Config:
        from_attributes = True
