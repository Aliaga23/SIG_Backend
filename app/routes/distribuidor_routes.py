from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.distribuidor_schema import (
    DistribuidorCreate, DistribuidorUpdate, DistribuidorOut
)
from app.services import distribuidor_service

router = APIRouter(
    prefix="/distribuidores",
    tags=["Distribuidores"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=DistribuidorOut)
def crear_distribuidor(distribuidor: DistribuidorCreate, db: Session = Depends(get_db)):
    return distribuidor_service.crear_distribuidor(db, distribuidor)

@router.get("", response_model=list[DistribuidorOut])
def listar_distribuidores(db: Session = Depends(get_db)):
    return distribuidor_service.obtener_distribuidores(db)

@router.get("/{id}", response_model=DistribuidorOut)
def obtener_distribuidor(id: UUID, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.obtener_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.put("/{id}", response_model=DistribuidorOut)
def actualizar_distribuidor(id: UUID, datos: DistribuidorUpdate, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.actualizar_distribuidor(db, id, datos)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.patch("/{id}/activo", response_model=DistribuidorOut)
def cambiar_estado_distribuidor(id: UUID, activo: bool, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.cambiar_estado_distribuidor(db, id, activo)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.patch("/{id}/ubicacion")
def actualizar_ubicacion_distribuidor(
    id: UUID, 
    latitud: float,
    longitud: float,
    db: Session = Depends(get_db)
):
    distribuidor = distribuidor_service.obtener_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    
    distribuidor.latitud = latitud
    distribuidor.longitud = longitud
    db.commit()
    db.refresh(distribuidor)
    return distribuidor

@router.delete("/{id}")
def eliminar_distribuidor(id: UUID, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.eliminar_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return {"mensaje": "Distribuidor eliminado correctamente"}
