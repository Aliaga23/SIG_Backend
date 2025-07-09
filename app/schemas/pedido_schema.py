from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

# DetallePedido
class DetallePedidoCreate(BaseModel):
    producto_id: UUID
    cantidad: int

class DetallePedidoOut(DetallePedidoCreate):
    id: UUID

    class Config:
        from_attributes = True

# Pedido
class PedidoBase(BaseModel):
    instrucciones_entrega: str | None = None

class PedidoCreate(PedidoBase):
    cliente_id: UUID
    detalles: list[DetallePedidoCreate]

class PedidoOut(PedidoBase):
    id: UUID
    fecha_pedido: datetime
    estado: str
    total: float
    cliente_id: UUID
    detalles: list[DetallePedidoOut]

    class Config:
        from_attributes = True

class PedidoEstadoUpdate(BaseModel):
    estado: str
