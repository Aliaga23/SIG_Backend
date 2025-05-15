from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

class Vehiculo(Base):
    __tablename__ = "vehiculo"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    marca = Column(String(50), nullable=False)
    modelo = Column(String(50), nullable=False)
    placa = Column(String(20), unique=True, nullable=False)
    capacidad_carga = Column(Integer, nullable=False)
    tipo_vehiculo = Column(String(50), nullable=False)
    anio = Column(Integer, nullable=False)
