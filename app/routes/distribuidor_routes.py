from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.distribuidor_schema import (
    DistribuidorCreate, DistribuidorUpdate, DistribuidorOut, CambiarEstadoRequest
)
from app.services import distribuidor_service
from app.auth.dependencies import get_current_distribuidor
from app.models.distribuidor_model import Distribuidor
from app.models.asignacion_vehiculo_model import AsignacionVehiculo
from app.models.vehiculo_model import Vehiculo

security = HTTPBearer()

router = APIRouter(
    prefix="/distribuidores",
    tags=["Distribuidores"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=DistribuidorOut)
def crear_distribuidor(distribuidor: DistribuidorCreate, db: Session = Depends(get_db)):
    return distribuidor_service.crear_distribuidor(db, distribuidor)

@router.get("", response_model=list[DistribuidorOut])
def listar_distribuidores(db: Session = Depends(get_db)):
    return distribuidor_service.obtener_distribuidores(db)

@router.get("/mi-perfil", dependencies=[Depends(security)])
def obtener_mi_perfil(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Obtiene el perfil completo del distribuidor autenticado con todos sus datos personales,
    información del vehículo, estadísticas y datos relevantes.
    """
    from app.models.asignacion_model import AsignacionEntrega
    from datetime import datetime, date
    
    # Información básica del distribuidor
    perfil_basico = {
        "id": distribuidor_actual.id,
        "nombre": distribuidor_actual.nombre,
        "apellido": distribuidor_actual.apellido,
        "nombre_completo": f"{distribuidor_actual.nombre} {distribuidor_actual.apellido}",
        "carnet": distribuidor_actual.carnet,
        "telefono": distribuidor_actual.telefono,
        "email": distribuidor_actual.email,
        "licencia": distribuidor_actual.licencia,
        "activo": distribuidor_actual.activo,
        "estado": distribuidor_actual.estado,
        "ubicacion": {
            "latitud": distribuidor_actual.latitud,
            "longitud": distribuidor_actual.longitud,
            "coordenadas": f"{distribuidor_actual.latitud},{distribuidor_actual.longitud}" if distribuidor_actual.latitud and distribuidor_actual.longitud else None
        }
    }
    
    # Información del vehículo asignado
    vehiculo_asignado = db.query(AsignacionVehiculo).filter(
        AsignacionVehiculo.id_distribuidor == distribuidor_actual.id
    ).first()
    
    vehiculo_info = None
    if vehiculo_asignado:
        vehiculo = db.query(Vehiculo).filter(
            Vehiculo.id == vehiculo_asignado.id_vehiculo
        ).first()
        
        if vehiculo:
            vehiculo_info = {
                "id": vehiculo.id,
                "marca": vehiculo.marca,
                "modelo": vehiculo.modelo,
                "placa": vehiculo.placa,
                "capacidad_carga": vehiculo.capacidad_carga,
                "tipo_vehiculo": vehiculo.tipo_vehiculo,
                "anio": vehiculo.anio,
                "descripcion_completa": f"{vehiculo.marca} {vehiculo.modelo} ({vehiculo.anio}) - {vehiculo.placa}"
            }
    
    # Estadísticas de asignaciones
    # Total de asignaciones
    total_asignaciones = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).count()
    
    # Asignaciones por estado
    asignaciones_pendientes = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "pendiente"
    ).count()
    
    asignaciones_aceptadas = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "aceptada"
    ).count()
    
    asignaciones_rechazadas = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "rechazada"
    ).count()
    
    # Asignaciones de hoy
    hoy = date.today()
    asignaciones_hoy = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.fecha_asignacion >= hoy
    ).count()
    
    # Estadísticas de entregas
    from app.models.ruta_entrega_model import Entrega
    
    # Total de entregas
    total_entregas = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).count()
    
    # Entregas completadas
    entregas_completadas = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        Entrega.estado == "entregado"
    ).count()
    
    # Entregas pendientes
    entregas_pendientes = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        Entrega.estado == "pendiente"
    ).count()
    
    # Entregas fallidas
    entregas_fallidas = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        Entrega.estado == "fallido"
    ).count()
    
    estadisticas = {
        "asignaciones": {
            "total": total_asignaciones,
            "pendientes": asignaciones_pendientes,
            "aceptadas": asignaciones_aceptadas,
            "rechazadas": asignaciones_rechazadas,
            "hoy": asignaciones_hoy
        },
        "entregas": {
            "total": total_entregas,
            "completadas": entregas_completadas,
            "pendientes": entregas_pendientes,
            "fallidas": entregas_fallidas,
            "tasa_exito": round((entregas_completadas / total_entregas * 100), 2) if total_entregas > 0 else 0
        }
    }
    
    # Estado actual
    estado_actual = {
        "tiene_vehiculo": vehiculo_info is not None,
        "puede_trabajar": distribuidor_actual.activo and vehiculo_info is not None,
        "estado_distribuidor": distribuidor_actual.estado,
        "disponible_para_asignaciones": distribuidor_actual.estado == "disponible" and distribuidor_actual.activo and vehiculo_info is not None,
        "asignaciones_pendientes_disponibles": asignaciones_pendientes > 0,
        "ubicacion_configurada": distribuidor_actual.latitud is not None and distribuidor_actual.longitud is not None
    }
    
    return {
        "perfil": perfil_basico,
        "vehiculo": vehiculo_info,
        "estadisticas": estadisticas,
        "estado": estado_actual,
        "ultima_actualizacion": datetime.now().isoformat()
    }

@router.get("/{id}", response_model=DistribuidorOut)
def obtener_distribuidor(id: UUID, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.obtener_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.put("/{id}", response_model=DistribuidorOut)
def actualizar_distribuidor(id: UUID, datos: DistribuidorUpdate, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.actualizar_distribuidor(db, id, datos)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.patch("/{id}/activo", response_model=DistribuidorOut)
def cambiar_estado_distribuidor(id: UUID, activo: bool, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.cambiar_estado_distribuidor(db, id, activo)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return distribuidor

@router.patch("/{id}/ubicacion")
def actualizar_ubicacion_distribuidor(
    id: UUID, 
    latitud: float,
    longitud: float,
    db: Session = Depends(get_db)
):
    distribuidor = distribuidor_service.obtener_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    
    distribuidor.latitud = latitud
    distribuidor.longitud = longitud
    db.commit()
    db.refresh(distribuidor)
    return distribuidor

@router.delete("/{id}")
def eliminar_distribuidor(id: UUID, db: Session = Depends(get_db)):
    distribuidor = distribuidor_service.eliminar_distribuidor(db, id)
    if not distribuidor:
        raise HTTPException(status_code=404, detail="Distribuidor no encontrado")
    return {"mensaje": "Distribuidor eliminado correctamente"}

@router.patch("/cambiar-estado", dependencies=[Depends(security)])
def cambiar_estado_distribuidor(
    estado_request: CambiarEstadoRequest,
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Permite al distribuidor cambiar su estado entre 'disponible', 'ocupado' e 'inactivo'.
    """
    estado_anterior = distribuidor_actual.estado
    nuevo_estado = estado_request.estado
    
    # Validar transiciones de estado
    if estado_anterior == nuevo_estado:
        return {
            "mensaje": f"El distribuidor ya está en estado {nuevo_estado}",
            "estado_anterior": estado_anterior,
            "estado_actual": nuevo_estado,
            "cambio_realizado": False
        }
    
    # Actualizar el estado
    distribuidor_actual.estado = nuevo_estado
    db.commit()
    
    return {
        "mensaje": f"Estado cambiado exitosamente de '{estado_anterior}' a '{nuevo_estado}'",
        "estado_anterior": estado_anterior,
        "estado_actual": nuevo_estado,
        "cambio_realizado": True,
        "distribuidor_id": distribuidor_actual.id,
        "disponible_para_asignaciones": nuevo_estado == "disponible" and distribuidor_actual.activo
    }


