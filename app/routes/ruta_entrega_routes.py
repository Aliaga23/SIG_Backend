from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.ruta_entrega_schema import (
    RutaEntregaOut,
    EntregaOut
)
from app.services import ruta_entrega_service

router = APIRouter(
    prefix="/rutas-entrega",
    tags=["Rutas y Entregas"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[RutaEntregaOut])
def listar_rutas(db: Session = Depends(get_db)):
    return ruta_entrega_service.listar_rutas_entrega(db)


@router.get("/entregas", response_model=list[EntregaOut])
def listar_entregas(db: Session = Depends(get_db)):
    return ruta_entrega_service.listar_entregas(db)

@router.get("/{ruta_id}", response_model=RutaEntregaOut)
def obtener_ruta(ruta_id: UUID, db: Session = Depends(get_db)):
    ruta = ruta_entrega_service.obtener_ruta_entrega(db, ruta_id)
    if not ruta:
        raise HTTPException(status_code=404, detail="Ruta no encontrada")
    return ruta

@router.get("/entregas/{entrega_id}", response_model=EntregaOut)
def obtener_entrega(entrega_id: UUID, db: Session = Depends(get_db)):
    entrega = ruta_entrega_service.obtener_entrega(db, entrega_id)
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return entrega
