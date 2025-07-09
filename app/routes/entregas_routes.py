from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.schemas.entrega_schema import EntregaUpdate
from app.schemas.ruta_entrega_schema import EntregaOut
from app.services.entregas_service import completar_entrega

router = APIRouter(prefix="/entregas", tags=["Entregas"])
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.patch("/{entrega_id}", response_model=EntregaOut)
def patch_entrega(entrega_id: UUID, payload: EntregaUpdate, db: Session = Depends(get_db)):
    ent = completar_entrega(db, entrega_id, payload)
    if not ent:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")
    return ent
