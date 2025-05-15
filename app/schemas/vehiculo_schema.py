from pydantic import BaseModel
from uuid import UUID

class VehiculoBase(BaseModel):
    marca: str
    modelo: str
    placa: str
    capacidad_carga: int
    tipo_vehiculo: str
    anio: int

class VehiculoCreate(VehiculoBase):
    pass

class VehiculoUpdate(VehiculoBase):
    pass

class VehiculoOut(VehiculoBase):
    id: UUID

    class Config:
        from_attributes = True
