from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.asignacion_schema import (
    AsignacionEntregaCreate, AsignacionEntregaOut,
    PedidoAsignadoCreate, PedidoAsignadoOut
)
from app.services import asignacion_service

router = APIRouter(
    prefix="/asignaciones-entrega",
    tags=["Asignaciones de Entrega"]
)

# ---------------------------
# DB Dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------------------------
# ASIGNACION ENTREGA
# ---------------------------

@router.post("", response_model=AsignacionEntregaOut)
def crear_asignacion(datos: AsignacionEntregaCreate, db: Session = Depends(get_db)):
    return asignacion_service.crear_asignacion_entrega(db, datos)

@router.get("", response_model=list[AsignacionEntregaOut])
def listar_asignaciones(db: Session = Depends(get_db)):
    return asignacion_service.listar_asignaciones(db)

@router.get("/{asignacion_id}", response_model=AsignacionEntregaOut)
def obtener_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    asignacion = asignacion_service.obtener_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion

@router.delete("/{asignacion_id}")
def eliminar_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    asignacion = asignacion_service.eliminar_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return {"mensaje": "Asignación eliminada correctamente"}

# ---------------------------
# PEDIDOS ASIGNADOS
# ---------------------------

@router.post("/pedidos", response_model=PedidoAsignadoOut)
def asignar_pedido(datos: PedidoAsignadoCreate, db: Session = Depends(get_db)):
    return asignacion_service.asignar_pedido_a_entrega(db, datos)

@router.get("/{asignacion_id}/pedidos", response_model=list[PedidoAsignadoOut])
def listar_pedidos(asignacion_id: UUID, db: Session = Depends(get_db)):
    return asignacion_service.listar_pedidos_asignados_por_asignacion(db, asignacion_id)

@router.delete("/pedidos/{pedido_asignado_id}")
def eliminar_pedido_asignado(pedido_asignado_id: UUID, db: Session = Depends(get_db)):
    deleted = asignacion_service.eliminar_pedido_asignado(db, pedido_asignado_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pedido asignado no encontrado")
    return {"mensaje": "Pedido asignado eliminado correctamente"}

@router.post("/asignar-automaticamente/{distribuidor_id}", response_model=AsignacionEntregaOut)
def asignar_automaticamente(distribuidor_id: UUID, db: Session = Depends(get_db)):
    try:
        return asignacion_service.asignacion_automatica(db, distribuidor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
