from sqlalchemy import Column, String, ForeignKey, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class RutaEntrega(Base):
    __tablename__ = "ruta_entrega"

    ruta_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coordenadas_inicio = Column(String(100), nullable=False)  # Ej: "-17.78,-63.18"
    coordenadas_fin = Column(String(100), nullable=False)
    distancia = Column(Numeric(10, 2), nullable=True)  # En km
    tiempo_estimado = Column(String(50), nullable=True)  # Ej: "35 mins"

    entregas = relationship("Entrega", back_populates="ruta", cascade="all, delete")


class Entrega(Base):
    __tablename__ = "entrega"

    id_entrega = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fecha_hora_entrega = Column(TIMESTAMP, default=datetime.utcnow)
    coordenadas_fin = Column(String(100), nullable=True)
    estado = Column(String(50), default="pendiente")  # entregado, no entregado, producto incorrecto, etc.
    observaciones = Column(String, nullable=True)

    ruta_id = Column(UUID(as_uuid=True), ForeignKey("ruta_entrega.ruta_id", ondelete="SET NULL"))
    pedido_asignado_id = Column(UUID(as_uuid=True), unique=True)  # ID del pedido asignado

    ruta = relationship("RutaEntrega", back_populates="entregas")
