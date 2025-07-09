from sqlalchemy import Column, ForeignKey, TIMESTAMP, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database import Base

class AsignacionEntrega(Base):
    __tablename__ = "asignacion_entrega"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fecha_asignacion = Column(TIMESTAMP, default=datetime.utcnow)
    id_distribuidor = Column(UUID(as_uuid=True), ForeignKey("distribuidor.id", ondelete="SET NULL"))
    ruta_id = Column(UUID(as_uuid=True), ForeignKey("ruta_entrega.ruta_id", ondelete="SET NULL"))
    estado = Column(String(20), default="pendiente")  # pendiente, aceptada, rechazada

    pedidos_asignados = relationship(
        "PedidoAsignado",
        back_populates="asignacion",
        cascade="all, delete"
    )
    entregas = relationship(
        "Entrega",
        back_populates="asignacion",
        cascade="all, delete-orphan"
    )

class PedidoAsignado(Base):
    __tablename__ = "pedido_asignado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id", ondelete="CASCADE"))
    asignacion_id = Column(UUID(as_uuid=True), ForeignKey("asignacion_entrega.id", ondelete="CASCADE"))

    asignacion = relationship("AsignacionEntrega", back_populates="pedidos_asignados")
