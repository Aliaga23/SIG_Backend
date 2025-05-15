from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.asignacion_vehiculo_schema import AsignacionVehiculoCreate, AsignacionVehiculoOut
from app.services import asignacion_vehiculo_service

router = APIRouter(
    prefix="/asignaciones-vehiculo",
    tags=["Asignaciones de Vehículo"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=AsignacionVehiculoOut)
def asignar_vehiculo(datos: AsignacionVehiculoCreate, db: Session = Depends(get_db)):
    return asignacion_vehiculo_service.crear_asignacion(db, datos)

@router.get("", response_model=list[AsignacionVehiculoOut])
def listar_asignaciones(db: Session = Depends(get_db)):
    return asignacion_vehiculo_service.listar_asignaciones(db)

@router.delete("")
def eliminar_asignacion(id_vehiculo: UUID, id_distribuidor: UUID, db: Session = Depends(get_db)):
    deleted = asignacion_vehiculo_service.eliminar_asignacion(db, id_vehiculo, id_distribuidor)
    if not deleted:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {"mensaje": "Asignación eliminada correctamente"}
