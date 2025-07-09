from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.tienda_model import Tienda
from app.schemas.tienda_schema import TiendaCreate, TiendaResponse, TiendaUpdate
from app.services.tienda_service import get_tiendas, get_tienda, create_tienda, update_tienda, delete_tienda

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/tiendas/", response_model=TiendaResponse, status_code=status.HTTP_201_CREATED)
def create_tienda_route(
    tienda: TiendaCreate, 
    db: Session = Depends(get_db)
):
    return create_tienda(db=db, tienda=tienda)

@router.get("/tiendas/", response_model=List[TiendaResponse])
def read_tiendas(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    tiendas = get_tiendas(db, skip=skip, limit=limit)
    return tiendas

@router.get("/tiendas/{tienda_id}", response_model=TiendaResponse)
def read_tienda(
    tienda_id: UUID, 
    db: Session = Depends(get_db)
):
    db_tienda = get_tienda(db, tienda_id=tienda_id)
    if db_tienda is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return db_tienda

@router.put("/tiendas/{tienda_id}", response_model=TiendaResponse)
def update_tienda_route(
    tienda_id: UUID, 
    tienda: TiendaUpdate, 
    db: Session = Depends(get_db)
):
    db_tienda = update_tienda(db, tienda_id=tienda_id, tienda=tienda)
    if db_tienda is None:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return db_tienda

@router.delete("/tiendas/{tienda_id}", response_model=dict)
def delete_tienda_route(
    tienda_id: UUID, 
    db: Session = Depends(get_db)
):
    success = delete_tienda(db, tienda_id=tienda_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tienda no encontrada")
    return {"detail": "Tienda eliminada correctamente"}
