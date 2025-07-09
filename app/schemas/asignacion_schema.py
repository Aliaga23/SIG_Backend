from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class PedidoAsignadoBase(BaseModel):
    pedido_id: UUID

class PedidoAsignadoCreate(PedidoAsignadoBase):
    asignacion_id: UUID

class PedidoAsignadoOut(PedidoAsignadoBase):
    id: UUID
    asignacion_id: UUID

    class Config:
        from_attributes = True


class AsignacionEntregaBase(BaseModel):
    id_distribuidor: UUID
    ruta_id: UUID
    estado: Optional[str] = "pendiente"

class AsignacionEntregaCreate(AsignacionEntregaBase):
    pass

class AsignacionEntregaOut(AsignacionEntregaBase):
    id: UUID
    fecha_asignacion: datetime
    pedidos_asignados: list[PedidoAsignadoOut] = []

    class Config:
        from_attributes = True


class AsignacionAutomaticaRequest(BaseModel):
    pedidos_ids: Optional[list[UUID]] = None
    radio_maximo_km: Optional[float] = 5.0
