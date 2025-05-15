from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.ruta_entrega_schema import (
    RutaEntregaCreate, RutaEntregaOut,
    EntregaCreate, EntregaOut,
    EntregaEstadoUpdate, EntregaObservacionesUpdate, EntregaUbicacionUpdate
)
from app.services import ruta_entrega_service

router = APIRouter(
    prefix="/rutas-entrega",
    tags=["Rutas y Entregas"]
)

# ---------------------
# DB Dependency
# ---------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------
# RutaEntrega
# ---------------------
@router.post("", response_model=RutaEntregaOut)
def crear_ruta(ruta: RutaEntregaCreate, db: Session = Depends(get_db)):
    return ruta_entrega_service.crear_ruta_entrega(db, ruta)

@router.get("", response_model=list[RutaEntregaOut])
def listar_rutas(db: Session = Depends(get_db)):
    return ruta_entrega_service.listar_rutas_entrega(db)

@router.get("/{ruta_id}", response_model=RutaEntregaOut)
def obtener_ruta(ruta_id: UUID, db: Session = Depends(get_db)):
    ruta = ruta_entrega_service.obtener_ruta_entrega(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    return ruta

# ---------------------
# Entrega
# ---------------------
@router.post("/entregas", response_model=EntregaOut)
def registrar_entrega(entrega: EntregaCreate, db: Session = Depends(get_db)):
    return ruta_entrega_service.registrar_entrega(db, entrega)

@router.get("/entregas", response_model=list[EntregaOut])
def listar_entregas(db: Session = Depends(get_db)):
    return ruta_entrega_service.listar_entregas(db)

@router.get("/entregas/{entrega_id}", response_model=EntregaOut)
def obtener_entrega(entrega_id: UUID, db: Session = Depends(get_db)):
    entrega = ruta_entrega_service.obtener_entrega(db, entrega_id)
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return entrega

@router.patch("/entregas/{entrega_id}/estado", response_model=EntregaOut)
def cambiar_estado(entrega_id: UUID, body: EntregaEstadoUpdate, db: Session = Depends(get_db)):
    return ruta_entrega_service.actualizar_estado_entrega(db, entrega_id, body.estado)

@router.patch("/entregas/{entrega_id}/observaciones", response_model=EntregaOut)
def actualizar_observaciones(entrega_id: UUID, body: EntregaObservacionesUpdate, db: Session = Depends(get_db)):
    return ruta_entrega_service.actualizar_observaciones_entrega(db, entrega_id, body.observaciones)

@router.patch("/entregas/{entrega_id}/ubicacion", response_model=EntregaOut)
def actualizar_ubicacion(entrega_id: UUID, body: EntregaUbicacionUpdate, db: Session = Depends(get_db)):
    return ruta_entrega_service.actualizar_ubicacion_entrega(db, entrega_id, body.coordenadas_fin)
