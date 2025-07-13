from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.cliente_schema import ClienteCreate, ClienteUpdate, ClienteOut
from app.services import cliente_service
from app.auth.dependencies import get_current_cliente
from app.models.cliente_model import Cliente

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=ClienteOut)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    return cliente_service.crear_cliente(db, cliente)

@router.get("", response_model=list[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return cliente_service.listar_clientes(db)

@router.get("/{id}", response_model=ClienteOut)
def obtener_cliente(id: UUID, db: Session = Depends(get_db)):
    cliente = cliente_service.obtener_cliente(db, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{id}", response_model=ClienteOut)
def actualizar_cliente(id: UUID, datos: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = cliente_service.actualizar_cliente(db, id, datos)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.delete("/{id}")
def eliminar_cliente(id: UUID, db: Session = Depends(get_db)):
    cliente = cliente_service.eliminar_cliente(db, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado correctamente"}

@router.get("/perfil", response_model=ClienteOut)
def obtener_perfil_cliente(cliente_actual: Cliente = Depends(get_current_cliente)):
    """
    Endpoint protegido que requiere autenticación Bearer.
    Retorna el perfil del cliente autenticado.
    """
    return cliente_actual
