from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.schemas.cliente_schema import ClienteOut
from app.schemas.pedido_schema import PedidoOut


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

# Schemas para el endpoint de entregas del distribuidor

class EntregaDistribuidorOut(BaseModel):
    id_entrega: UUID
    fecha_hora_reg: datetime
    coordenadas_fin: str | None = None
    estado: str
    observaciones: str | None = None
    orden_entrega: int
    
    # Información del cliente
    cliente: ClienteOut | None = None
    
    # Información del pedido
    pedido: PedidoOut | None = None
    
    class Config:
        from_attributes = True

class RutaEntregaDistribuidorOut(BaseModel):
    ruta_id: UUID
    coordenadas_inicio: str
    coordenadas_fin: str
    distancia: float | None = None
    tiempo_estimado: str | None = None
    
    # Lista de entregas ordenadas
    entregas: list[EntregaDistribuidorOut] = []
    
    class Config:
        from_attributes = True

class AsignacionEntregaOut(BaseModel):
    id: UUID
    fecha_asignacion: datetime
    estado: str
    
    # Información de la ruta
    ruta: RutaEntregaDistribuidorOut | None = None
    
    class Config:
        from_attributes = True
