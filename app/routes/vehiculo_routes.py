from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.vehiculo_schema import VehiculoCreate, VehiculoUpdate, VehiculoOut
from app.services import vehiculo_service

router = APIRouter(
    prefix="/vehiculos",
    tags=["Vehiculos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=VehiculoOut)
def crear_vehiculo(vehiculo: VehiculoCreate, db: Session = Depends(get_db)):
    return vehiculo_service.crear_vehiculo(db, vehiculo)

@router.get("", response_model=list[VehiculoOut])
def listar_vehiculos(db: Session = Depends(get_db)):
    return vehiculo_service.listar_vehiculos(db)

@router.get("/{id}", response_model=VehiculoOut)
def obtener_vehiculo(id: UUID, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.obtener_vehiculo(db, id)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo

@router.put("/{id}", response_model=VehiculoOut)
def actualizar_vehiculo(id: UUID, datos: VehiculoUpdate, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.actualizar_vehiculo(db, id, datos)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return vehiculo

@router.delete("/{id}")
def eliminar_vehiculo(id: UUID, db: Session = Depends(get_db)):
    vehiculo = vehiculo_service.eliminar_vehiculo(db, id)
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado")
    return {"mensaje": "Vehículo eliminado correctamente"}
