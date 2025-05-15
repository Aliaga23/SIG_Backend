from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

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

class AsignacionEntregaCreate(AsignacionEntregaBase):
    pass

class AsignacionEntregaOut(AsignacionEntregaBase):
    id: UUID
    fecha_asignacion: datetime
    pedidos_asignados: list[PedidoAsignadoOut] = []

    class Config:
        from_attributes = True
