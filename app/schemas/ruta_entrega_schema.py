from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class EntregaBase(BaseModel):
    coordenadas_fin: str | None = None
    estado: str = "pendiente"
    observaciones: str | None = None

class EntregaCreate(EntregaBase):
    ruta_id: UUID
    pedido_asignado_id: UUID

class EntregaOut(EntregaBase):
    id_entrega: UUID
    fecha_hora_reg: datetime
    ruta_id: UUID
    pedido_id: UUID

    class Config:
        from_attributes = True

class EntregaEstadoUpdate(BaseModel):
    estado: str

class EntregaObservacionesUpdate(BaseModel):
    observaciones: str

class EntregaUbicacionUpdate(BaseModel):
    coordenadas_fin: str

class RutaEntregaBase(BaseModel):
    coordenadas_inicio: str
    coordenadas_fin: str
    distancia: float | None = None
    tiempo_estimado: str | None = None

class RutaEntregaCreate(RutaEntregaBase):
    pass

class RutaEntregaOut(RutaEntregaBase):
    ruta_id: UUID
    entregas: list[EntregaOut] = []

    class Config:
        from_attributes = True
