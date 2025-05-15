from sqlalchemy import Column, String, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Producto(Base):
    __tablename__ = "producto"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String, nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    talla = Column(String(10), nullable=True)
    color = Column(String(50), nullable=True)
    stock = Column(Integer, nullable=False)
