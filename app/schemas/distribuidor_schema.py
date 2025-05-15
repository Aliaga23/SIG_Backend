from pydantic import BaseModel, EmailStr
from uuid import UUID

class DistribuidorBase(BaseModel):
    nombre: str
    apellido: str
    carnet: str
    telefono: str
    email: EmailStr
    licencia: str

class DistribuidorCreate(DistribuidorBase):
    password: str  # requerido para crear

class DistribuidorUpdate(DistribuidorBase):
    password: str  # también se podrá actualizar si se desea

class DistribuidorOut(DistribuidorBase):
    id: UUID
    activo: bool

    class Config:
        from_attributes = True
