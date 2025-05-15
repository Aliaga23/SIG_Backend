from sqlalchemy import Column, ForeignKey, String, Numeric, TIMESTAMP, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class Pedido(Base):
    __tablename__ = "pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fecha_pedido = Column(TIMESTAMP, default=datetime.utcnow)
    estado = Column(String(50), default="pendiente")
    total = Column(Numeric(10, 2), default=0.0)
    instrucciones_entrega = Column(String, nullable=True)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("cliente.id", ondelete="SET NULL"))

    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete")

class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id", ondelete="CASCADE"))
    producto_id = Column(UUID(as_uuid=True), ForeignKey("producto.id", ondelete="SET NULL"))

    pedido = relationship("Pedido", back_populates="detalles")
