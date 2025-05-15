from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.pedido_schema import PedidoCreate, PedidoOut, PedidoEstadoUpdate
from app.services import pedido_service

router = APIRouter(
    prefix="/pedidos",
    tags=["Pedidos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=PedidoOut)
def crear_pedido(pedido: PedidoCreate, db: Session = Depends(get_db)):
    return pedido_service.crear_pedido(db, pedido)

@router.get("", response_model=list[PedidoOut])
def listar_pedidos(db: Session = Depends(get_db)):
    return pedido_service.listar_pedidos(db)

@router.get("/{id}", response_model=PedidoOut)
def obtener_pedido(id: UUID, db: Session = Depends(get_db)):
    pedido = pedido_service.obtener_pedido(db, id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

@router.patch("/{id}/estado", response_model=PedidoOut)
def actualizar_estado(id: UUID, body: PedidoEstadoUpdate, db: Session = Depends(get_db)):
    pedido = pedido_service.actualizar_estado_pedido(db, id, body.estado)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return pedido

@router.delete("/{id}")
def eliminar_pedido(id: UUID, db: Session = Depends(get_db)):
    pedido = pedido_service.eliminar_pedido(db, id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")
    return {"mensaje": "Pedido eliminado correctamente"}
