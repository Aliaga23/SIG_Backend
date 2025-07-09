from sqlalchemy import Column, String, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Distribuidor(Base):
    __tablename__ = "distribuidor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    carnet = Column(String(20), unique=True, nullable=False)
    telefono = Column(String(20), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    licencia = Column(String(50), nullable=False)
    password = Column(String(255), nullable=False)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    activo = Column(Boolean, default=True)
