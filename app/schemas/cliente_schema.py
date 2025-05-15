from pydantic import BaseModel, EmailStr
from uuid import UUID

class ClienteBase(BaseModel):
    nombre: str
    apellido: str
    telefono: str
    email: EmailStr
    direccion: str
    coordenadas: str | None = None

class ClienteCreate(ClienteBase):
    password: str

class ClienteUpdate(ClienteBase):
    password: str

class ClienteOut(ClienteBase):
    id: UUID

    class Config:
        from_attributes = True
