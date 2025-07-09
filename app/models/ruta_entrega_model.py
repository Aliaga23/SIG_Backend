# app/models/ruta_entrega_model.py
# --------------------------------
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, ForeignKey, Numeric, TIMESTAMP, Integer, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.asignacion_model import AsignacionEntrega


class RutaEntrega(Base):
    """
    Cabecera de la ruta. Contiene sólo el tramo global
    Tienda → … → Último cliente + meta-datos (km, tiempo).
    """
    __tablename__ = "ruta_entrega"

    ruta_id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coordenadas_inicio = Column(String(100), nullable=False)  
    coordenadas_fin    = Column(String(100), nullable=False)
    distancia          = Column(Numeric(10, 2), nullable=True) 
    tiempo_estimado    = Column(String(50),  nullable=True)    

    entregas = relationship(
        "Entrega",
        back_populates="ruta",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Entrega(Base):
    """
    Una parada dentro de la ruta:
      • referencia al Cliente
      • referencia (opcional) al Pedido — 1:1
    """
    __tablename__ = "entrega"
    __table_args__ = (
        UniqueConstraint("pedido_id", name="uq_entrega_pedido"),  
    )

    id_entrega        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fecha_hora_reg    = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    coordenadas_fin   = Column(String(100), nullable=True)         
    estado            = Column(String(50), default="pendiente")   
    observaciones     = Column(String, nullable=True)
    orden_entrega     = Column(Integer, nullable=False)            

    # ─── Relaciones ──────────────────────────────────────────────
    ruta_id           = Column(
        UUID(as_uuid=True),
        ForeignKey("ruta_entrega.ruta_id", ondelete="CASCADE"),
        nullable=False,
    )

    cliente_id        = Column(
        UUID(as_uuid=True),
        ForeignKey("cliente.id", ondelete="SET NULL"),
        nullable=True,
    )

    pedido_id         = Column(
        UUID(as_uuid=True),
        ForeignKey("pedido.id", ondelete="SET NULL"),
        nullable=True,
    )
    asignacion_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("asignacion_entrega.id", ondelete="CASCADE"),
        nullable=False
    )

    # backrefs
    ruta     = relationship("RutaEntrega", back_populates="entregas")
    cliente  = relationship("Cliente",     lazy="joined")
    pedido   = relationship("Pedido",      lazy="selectin")
    asignacion = relationship(
        "AsignacionEntrega",
        back_populates="entregas"
    )
