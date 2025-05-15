from sqlalchemy import Column, String, ForeignKey, Numeric, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.database import Base

class Pago(Base):
    __tablename__ = "pago"

    id_pago = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metodo_pago = Column(String(50), nullable=False)  # QR, Transferencia, Efectivo
    monto = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(50), default="pendiente")
    fecha_pago = Column(TIMESTAMP, default=datetime.utcnow)
    transaccion_id = Column(String(100), nullable=True)
    pedido_id = Column(UUID(as_uuid=True), ForeignKey("pedido.id", ondelete="CASCADE"), unique=True)
