from sqlalchemy.orm import Session
from uuid import UUID
from app.models.ruta_entrega_model import RutaEntrega, Entrega
from app.schemas.ruta_entrega_schema import RutaEntregaCreate, EntregaCreate

def crear_ruta_entrega(db: Session, datos: RutaEntregaCreate):
    nueva = RutaEntrega(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_rutas_entrega(db: Session):
    return db.query(RutaEntrega).all()

def obtener_ruta_entrega(db: Session, ruta_id: UUID):
    return db.query(RutaEntrega).filter(RutaEntrega.ruta_id == ruta_id).first()


def registrar_entrega(db: Session, datos: EntregaCreate):
    nueva = Entrega(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_entregas(db: Session):
    return db.query(Entrega).all()

def obtener_entrega(db: Session, entrega_id: UUID):
    return db.query(Entrega).filter(Entrega.id_entrega == entrega_id).first()

def actualizar_estado_entrega(db: Session, entrega_id: UUID, nuevo_estado: str):
    entrega = db.query(Entrega).filter(Entrega.id_entrega == entrega_id).first()
    if entrega:
        entrega.estado = nuevo_estado
        db.commit()
        db.refresh(entrega)
    return entrega

def actualizar_observaciones_entrega(db: Session, entrega_id: UUID, observaciones: str):
    entrega = db.query(Entrega).filter(Entrega.id_entrega == entrega_id).first()
    if entrega:
        entrega.observaciones = observaciones
        db.commit()
        db.refresh(entrega)
    return entrega

def actualizar_ubicacion_entrega(db: Session, entrega_id: UUID, coordenadas: str):
    entrega = db.query(Entrega).filter(Entrega.id_entrega == entrega_id).first()
    if entrega:
        entrega.coordenadas_fin = coordenadas
        db.commit()
        db.refresh(entrega)
    return entrega
