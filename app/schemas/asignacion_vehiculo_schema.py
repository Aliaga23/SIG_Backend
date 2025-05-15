from pydantic import BaseModel
from uuid import UUID

class AsignacionVehiculoCreate(BaseModel):
    id_vehiculo: UUID
    id_distribuidor: UUID

class AsignacionVehiculoOut(AsignacionVehiculoCreate):
    class Config:
        from_attributes = True
