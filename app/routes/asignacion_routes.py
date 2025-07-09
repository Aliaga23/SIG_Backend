from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import SessionLocal
from app.schemas.asignacion_schema import (
    AsignacionEntregaOut,
    PedidoAsignadoCreate, PedidoAsignadoOut,
    AsignacionAutomaticaRequest
)
from app.services import asignacion_service
from app.services.asignacion_service import asignacion_automatica_propuesta

router = APIRouter(
    prefix="/asignaciones-entrega",
    tags=["Asignaciones de Entrega"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[AsignacionEntregaOut])
def listar_asignaciones(db: Session = Depends(get_db)):
    return asignacion_service.listar_asignaciones(db)

@router.get("/{asignacion_id}", response_model=AsignacionEntregaOut)
def obtener_asignacion(asignacion_id: UUID, db: Session = Depends(get_db)):
    asignacion = asignacion_service.obtener_asignacion(db, asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion



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


@router.post("/{asignacion_id}/aceptar", response_model=AsignacionEntregaOut)
def aceptar_asignacion(asignacion_id: UUID, distribuidor_id: UUID, db: Session = Depends(get_db)):
    """Endpoint para que el distribuidor acepte una asignación pendiente"""
    try:
        return asignacion_service.aceptar_asignacion(db, asignacion_id, distribuidor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{asignacion_id}/rechazar", response_model=AsignacionEntregaOut)
def rechazar_asignacion(asignacion_id: UUID, distribuidor_id: UUID, db: Session = Depends(get_db)):
    """Endpoint para que el distribuidor rechace una asignación pendiente"""
    try:
        return asignacion_service.rechazar_asignacion(db, asignacion_id, distribuidor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/distribuidor/{distribuidor_id}/pendientes", response_model=list[AsignacionEntregaOut])
def listar_asignaciones_pendientes(distribuidor_id: UUID, db: Session = Depends(get_db)):
    """Lista las asignaciones pendientes para un distribuidor específico"""
    return asignacion_service.listar_asignaciones_pendientes(db, distribuidor_id)

@router.post("/asignar-pendientes", response_model=List[AsignacionEntregaOut])
def asignar_pendientes(
    pedidos_ids: List[UUID] = None,
    radio_maximo_km: float = 5.0,
    db: Session = Depends(get_db)
):
    """
    Asigna automáticamente todos los pedidos pendientes al distribuidor más cercano disponible.
    Simplificación del proceso para mayor facilidad de uso.
    """
    try:
         asignaciones = asignacion_automatica_propuesta(db, pedidos_ids, radio_maximo_km)
         return [AsignacionEntregaOut.from_orm(a) for a in asignaciones]
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))

@router.post("/verificar-expiradas", response_model=dict)
def verificar_asignaciones_expiradas(tiempo_limite_minutos: int = 30, db: Session = Depends(get_db)):
    """
    Verifica y maneja las asignaciones que han expirado (tiempo límite superado).
    Las asignaciones pendientes que superen el tiempo límite se marcan como expiradas
    y los pedidos vuelven a estar disponibles para asignación.
    
    Args:
        tiempo_limite_minutos: Tiempo en minutos que tiene un distribuidor para responder
    """
    try:
        expiradas = asignacion_service.verificar_asignaciones_expiradas(db, tiempo_limite_minutos)
        
        nuevas_asignaciones = []
        if expiradas:
            nuevas_asignaciones = asignacion_service.reasignar_pedidos_expirados(db)
        
        return {
            "asignaciones_expiradas": len(expiradas),
            "nuevas_asignaciones": len(nuevas_asignaciones),
            "mensaje": f"Se procesaron {len(expiradas)} asignaciones expiradas y se crearon {len(nuevas_asignaciones)} nuevas asignaciones."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
