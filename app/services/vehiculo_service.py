from sqlalchemy.orm import Session
from uuid import UUID
from app.models.vehiculo_model import Vehiculo
from app.schemas.vehiculo_schema import VehiculoCreate, VehiculoUpdate

def crear_vehiculo(db: Session, vehiculo: VehiculoCreate):
    nuevo = Vehiculo(**vehiculo.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def listar_vehiculos(db: Session):
    return db.query(Vehiculo).all()

def obtener_vehiculo(db: Session, vehiculo_id: UUID):
    return db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()

def actualizar_vehiculo(db: Session, vehiculo_id: UUID, datos: VehiculoUpdate):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if vehiculo:
        for key, value in datos.dict().items():
            setattr(vehiculo, key, value)
        db.commit()
        db.refresh(vehiculo)
    return vehiculo

def eliminar_vehiculo(db: Session, vehiculo_id: UUID):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id == vehiculo_id).first()
    if vehiculo:
        db.delete(vehiculo)
        db.commit()
    return vehiculo
