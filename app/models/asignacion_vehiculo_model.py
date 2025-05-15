from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class AsignacionVehiculo(Base):
    __tablename__ = "asignacion_vehiculo"

    id_vehiculo = Column(UUID(as_uuid=True), ForeignKey("vehiculo.id", ondelete="CASCADE"), primary_key=True)
    id_distribuidor = Column(UUID(as_uuid=True), ForeignKey("distribuidor.id", ondelete="CASCADE"), primary_key=True)
