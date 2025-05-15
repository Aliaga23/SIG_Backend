from sqlalchemy.orm import Session
from app.models.asignacion_vehiculo_model import AsignacionVehiculo
from app.schemas.asignacion_vehiculo_schema import AsignacionVehiculoCreate

def crear_asignacion(db: Session, datos: AsignacionVehiculoCreate):
    nueva = AsignacionVehiculo(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_asignaciones(db: Session):
    return db.query(AsignacionVehiculo).all()

def eliminar_asignacion(db: Session, id_vehiculo, id_distribuidor):
    asignacion = db.query(AsignacionVehiculo).filter_by(
        id_vehiculo=id_vehiculo,
        id_distribuidor=id_distribuidor
    ).first()
    if asignacion:
        db.delete(asignacion)
        db.commit()
    return asignacion
