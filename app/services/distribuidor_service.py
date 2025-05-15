import bcrypt
from sqlalchemy.orm import Session
from uuid import UUID
from app.models.distribuidor_model import Distribuidor
from app.schemas.distribuidor_schema import DistribuidorCreate, DistribuidorUpdate

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def crear_distribuidor(db: Session, distribuidor: DistribuidorCreate):
    hashed_pw = hash_password(distribuidor.password)
    nuevo = Distribuidor(**distribuidor.dict(exclude={"password"}), password=hashed_pw)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def obtener_distribuidores(db: Session):
    return db.query(Distribuidor).all()

def obtener_distribuidor(db: Session, distribuidor_id: UUID):
    return db.query(Distribuidor).filter(Distribuidor.id == distribuidor_id).first()

def actualizar_distribuidor(db: Session, distribuidor_id: UUID, datos: DistribuidorUpdate):
    dist = db.query(Distribuidor).filter(Distribuidor.id == distribuidor_id).first()
    if dist:
        for key, value in datos.dict().items():
            if key == "password":
                value = hash_password(value)
            setattr(dist, key, value)
        db.commit()
        db.refresh(dist)
    return dist

def cambiar_estado_distribuidor(db: Session, distribuidor_id: UUID, activo: bool):
    dist = db.query(Distribuidor).filter(Distribuidor.id == distribuidor_id).first()
    if dist:
        dist.activo = activo
        db.commit()
        db.refresh(dist)
    return dist

def eliminar_distribuidor(db: Session, distribuidor_id: UUID):
    dist = db.query(Distribuidor).filter(Distribuidor.id == distribuidor_id).first()
    if dist:
        db.delete(dist)
        db.commit()
    return dist
