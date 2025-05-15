from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class PagoBase(BaseModel):
    metodo_pago: str
    monto: float
    pedido_id: UUID

class PagoCreate(PagoBase):
    pass

class PagoOut(PagoBase):
    id_pago: UUID
    estado: str
    fecha_pago: datetime
    transaccion_id: str | None

    class Config:
        from_attributes = True

class PagoEstadoUpdate(BaseModel):
    estado: str
