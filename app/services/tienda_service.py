from sqlalchemy.orm import Session
from app.models.tienda_model import Tienda
from app.schemas.tienda_schema import TiendaCreate, TiendaUpdate
from uuid import UUID
from typing import List, Optional

def get_tiendas(db: Session, skip: int = 0, limit: int = 100) -> List[Tienda]:
    return db.query(Tienda).offset(skip).limit(limit).all()

def get_tienda(db: Session, tienda_id: UUID) -> Optional[Tienda]:
    return db.query(Tienda).filter(Tienda.id == tienda_id).first()

def create_tienda(db: Session, tienda: TiendaCreate) -> Tienda:
    db_tienda = Tienda(**tienda.dict())
    db.add(db_tienda)
    db.commit()
    db.refresh(db_tienda)
    return db_tienda

def update_tienda(db: Session, tienda_id: UUID, tienda: TiendaUpdate) -> Optional[Tienda]:
    db_tienda = db.query(Tienda).filter(Tienda.id == tienda_id).first()
    if not db_tienda:
        return None
        
    for key, value in tienda.dict(exclude_unset=True).items():
        setattr(db_tienda, key, value)
    
    db.commit()
    db.refresh(db_tienda)
    return db_tienda

def delete_tienda(db: Session, tienda_id: UUID) -> bool:
    db_tienda = db.query(Tienda).filter(Tienda.id == tienda_id).first()
    if not db_tienda:
        return False
        
    db.delete(db_tienda)
    db.commit()
    return True
