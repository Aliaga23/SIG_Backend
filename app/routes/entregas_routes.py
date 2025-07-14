from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from uuid import UUID
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from app.database import SessionLocal
from app.schemas.entrega_schema import EntregaUpdate
from app.schemas.ruta_entrega_schema import EntregaOut, AsignacionEntregaOut
from app.services.entregas_service import completar_entrega
from app.auth.dependencies import get_current_distribuidor
from app.models.distribuidor_model import Distribuidor
from app.models.asignacion_model import AsignacionEntrega, PedidoAsignado
from app.models.ruta_entrega_model import RutaEntrega, Entrega
from app.models.pedido_model import Pedido, DetallePedido
from app.models.cliente_model import Cliente
from app.models.tienda_model import Tienda
from app.models.vehiculo_model import Vehiculo
from app.models.asignacion_vehiculo_model import AsignacionVehiculo
from app.models.tienda_model import Tienda

security = HTTPBearer()

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

@router.get("/mis-entregas", response_model=list[AsignacionEntregaOut], dependencies=[Depends(security)])
def obtener_mis_entregas(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las asignaciones de entregas del distribuidor autenticado
    con el orden de las entregas, ubicación actual y próxima entrega.
    """
    asignaciones = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).all()
    
    if not asignaciones:
        return []
    
    ultima_entrega_completada = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        Entrega.estado == "entregado"
    ).order_by(Entrega.fecha_hora_reg.desc()).first()
    
    ubicacion_actual = None
    if ultima_entrega_completada and ultima_entrega_completada.coordenadas_fin:
        try:
            lat, lon = map(float, ultima_entrega_completada.coordenadas_fin.split(","))
            ubicacion_actual = {
                "latitud": lat,
                "longitud": lon,
                "descripcion": "Última entrega completada",
                "entrega_id": str(ultima_entrega_completada.id_entrega)
            }
        except (ValueError, TypeError):
            pass
    
    if not ubicacion_actual:
        tiendas = db.query(Tienda).filter(
            Tienda.latitud.isnot(None), 
            Tienda.longitud.isnot(None)
        ).all()
        
        if tiendas:
            tienda_inicial = min(tiendas, key=lambda t: geodesic(
                (distribuidor_actual.latitud, distribuidor_actual.longitud),
                (t.latitud, t.longitud)
            ).km)
            
            ubicacion_actual = {
                "latitud": tienda_inicial.latitud,
                "longitud": tienda_inicial.longitud,
                "descripcion": "Tienda de recogida",
                "tienda_nombre": tienda_inicial.nombre if hasattr(tienda_inicial, 'nombre') else "Tienda"
            }
    
    resultado = []
    for asignacion in asignaciones:
        ruta = db.query(RutaEntrega).filter(
            RutaEntrega.ruta_id == asignacion.ruta_id
        ).first()
        
        if ruta:
            entregas_ordenadas = db.query(Entrega).filter(
                Entrega.asignacion_id == asignacion.id
            ).order_by(Entrega.orden_entrega).all()
            
            proxima_entrega = None
            for entrega in entregas_ordenadas:
                if entrega.estado == "pendiente":
                    proxima_entrega = {
                        "id_entrega": entrega.id_entrega,
                        "orden_entrega": entrega.orden_entrega,
                        "coordenadas_fin": entrega.coordenadas_fin,
                        "cliente_id": entrega.cliente_id
                    }
                    break
            
            asignacion_data = {
                "id": asignacion.id,
                "fecha_asignacion": asignacion.fecha_asignacion,
                "estado": asignacion.estado,
                "ubicacion_actual": ubicacion_actual,
                "proxima_entrega": proxima_entrega,
                "ruta": {
                    "ruta_id": ruta.ruta_id,
                    "coordenadas_inicio": ruta.coordenadas_inicio,
                    "coordenadas_fin": ruta.coordenadas_fin,
                    "distancia": float(ruta.distancia) if ruta.distancia else None,
                    "tiempo_estimado": ruta.tiempo_estimado,
                    "entregas": [
                        {
                            "id_entrega": entrega.id_entrega,
                            "fecha_hora_reg": entrega.fecha_hora_reg,
                            "coordenadas_fin": entrega.coordenadas_fin,
                            "estado": entrega.estado,
                            "observaciones": entrega.observaciones,
                            "orden_entrega": entrega.orden_entrega,
                            "cliente": entrega.cliente,
                            "pedido": entrega.pedido
                        }
                        for entrega in entregas_ordenadas
                    ]
                }
            }
            resultado.append(asignacion_data)
    
    return resultado

@router.get("/mis-entregas-hoy", response_model=list[AsignacionEntregaOut], dependencies=[Depends(security)])
def obtener_mis_entregas_hoy(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Obtiene las asignaciones de entregas del distribuidor autenticado para el día de hoy
    con el orden de las entregas y toda la información necesaria.
    """
    from datetime import date
    
    # Buscar asignaciones del distribuidor actual de hoy
    hoy = date.today()
    asignaciones = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.fecha_asignacion >= hoy
    ).all()
    
    if not asignaciones:
        return []
    
    # Para cada asignación, obtenemos la ruta y las entregas ordenadas
    resultado = []
    for asignacion in asignaciones:
        # Obtener la ruta asociada
        ruta = db.query(RutaEntrega).filter(
            RutaEntrega.ruta_id == asignacion.ruta_id
        ).first()
        
        if ruta:
            # Obtener las entregas ordenadas por orden_entrega
            entregas_ordenadas = db.query(Entrega).filter(
                Entrega.asignacion_id == asignacion.id
            ).order_by(Entrega.orden_entrega).all()
            
            # Construir el objeto de respuesta
            asignacion_data = {
                "id": asignacion.id,
                "fecha_asignacion": asignacion.fecha_asignacion,
                "estado": asignacion.estado,
                "ruta": {
                    "ruta_id": ruta.ruta_id,
                    "coordenadas_inicio": ruta.coordenadas_inicio,
                    "coordenadas_fin": ruta.coordenadas_fin,
                    "distancia": float(ruta.distancia) if ruta.distancia else None,
                    "tiempo_estimado": ruta.tiempo_estimado,
                    "entregas": [
                        {
                            "id_entrega": entrega.id_entrega,
                            "fecha_hora_reg": entrega.fecha_hora_reg,
                            "coordenadas_fin": entrega.coordenadas_fin,
                            "estado": entrega.estado,
                            "observaciones": entrega.observaciones,
                            "orden_entrega": entrega.orden_entrega,
                            "cliente": entrega.cliente,
                            "pedido": entrega.pedido
                        }
                        for entrega in entregas_ordenadas
                    ]
                }
            }
            resultado.append(asignacion_data)
    
    return resultado

@router.patch("/asignacion/{asignacion_id}/aceptar", dependencies=[Depends(security)])
def aceptar_asignacion(
    asignacion_id: UUID,
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Permite al distribuidor autenticado aceptar una asignación de entregas.
    - Rechaza automáticamente la misma asignación para otros distribuidores
    - Verifica la capacidad del vehículo del distribuidor
    - Crea nuevas asignaciones si excede la capacidad
    """
    from app.models.asignacion_vehiculo_model import AsignacionVehiculo
    from app.models.vehiculo_model import Vehiculo
    from app.models.pedido_model import Pedido, DetallePedido
    
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == asignacion_id,
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=404, 
            detail="Asignación no encontrada o no pertenece a este distribuidor"
        )
    
    if asignacion.estado != "pendiente":
        raise HTTPException(
            status_code=400, 
            detail=f"La asignación ya está en estado: {asignacion.estado}"
        )
    
    vehiculo_asignado = db.query(AsignacionVehiculo).filter(
        AsignacionVehiculo.id_distribuidor == distribuidor_actual.id
    ).first()
    
    if not vehiculo_asignado:
        raise HTTPException(
            status_code=400,
            detail="No tienes un vehículo asignado"
        )
    
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id == vehiculo_asignado.id_vehiculo
    ).first()
    
    if not vehiculo:
        raise HTTPException(
            status_code=400,
            detail="Vehículo no encontrado"
        )
    
    # Obtener los pedidos asignados a esta asignación
    pedidos_asignados = db.query(PedidoAsignado).filter(
        PedidoAsignado.asignacion_id == asignacion.id
    ).all()
    
    if not pedidos_asignados:
        raise HTTPException(
            status_code=400,
            detail="No hay pedidos asignados a esta asignación"
        )
    
    # Verificar si ya existen entregas creadas
    entregas_existentes = db.query(Entrega).filter(
        Entrega.asignacion_id == asignacion.id
    ).all()
    
    total_cajas = 0
    pedidos_info = []
    
    # Si no existen entregas, crearlas basándose en los pedidos asignados
    if not entregas_existentes:
        # Obtener la ruta para crear las entregas
        ruta = db.query(RutaEntrega).filter(
            RutaEntrega.ruta_id == asignacion.ruta_id
        ).first()
        
        if not ruta:
            raise HTTPException(
                status_code=400,
                detail="No se encontró la ruta asociada a la asignación"
            )
        
        # Obtener tienda más cercana al distribuidor (punto de recogida)
        tiendas = db.query(Tienda).filter(
            Tienda.latitud.isnot(None), 
            Tienda.longitud.isnot(None)
        ).all()
        
        if not tiendas:
            raise HTTPException(
                status_code=400,
                detail="No hay tiendas disponibles con coordenadas"
            )
            
        tienda_inicial = min(tiendas, key=lambda t: geodesic(
            (distribuidor_actual.latitud, distribuidor_actual.longitud),
            (t.latitud, t.longitud)
        ).km)
        
        # Optimizar orden de entregas basado en la ubicación de la tienda
        punto_inicio = (tienda_inicial.latitud, tienda_inicial.longitud)
        pedidos_optimizados = _optimizar_orden_entregas(db, pedidos_asignados, punto_inicio)
        
        # Crear entregas para cada pedido asignado en orden optimizado
        for orden, pedido_asignado in enumerate(pedidos_optimizados, 1):
            pedido = db.query(Pedido).filter(Pedido.id == pedido_asignado.pedido_id).first()
            if pedido:
                cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
                if cliente:
                    # Crear la entrega
                    nueva_entrega = Entrega(
                        ruta_id=asignacion.ruta_id,
                        cliente_id=cliente.id,
                        pedido_id=pedido.id,
                        asignacion_id=asignacion.id,
                        coordenadas_fin=cliente.coordenadas,
                        orden_entrega=orden,
                        estado="pendiente"
                    )
                    db.add(nueva_entrega)
        
        db.commit()
        
        # Ahora obtener las entregas creadas
        entregas = db.query(Entrega).filter(
            Entrega.asignacion_id == asignacion.id
        ).all()
    else:
        entregas = entregas_existentes
    
    # Calcular el total de cajas
    for entrega in entregas:
        if entrega.pedido_id:
            # Contar detalles del pedido (cada detalle es una caja)
            detalles = db.query(DetallePedido).filter(
                DetallePedido.pedido_id == entrega.pedido_id
            ).all()
            
            cajas_pedido = sum(detalle.cantidad for detalle in detalles)
            total_cajas += cajas_pedido
            pedidos_info.append({
                "pedido_id": entrega.pedido_id,
                "entrega_id": entrega.id_entrega,
                "cajas": cajas_pedido
            })
    
    # Verificar capacidad del vehículo
    capacidad_vehiculo = vehiculo.capacidad_carga
    
    if total_cajas <= capacidad_vehiculo:
        # El vehículo puede con toda la asignación
        asignacion.estado = "aceptada"
        
        # Cambiar estado del distribuidor a ocupado
        distribuidor_actual.estado = "ocupado"
        
        # Cambiar estado de todos los pedidos asignados a "aceptado"
        pedidos_aceptados = []
        for info in pedidos_info:
            pedido = db.query(Pedido).filter(Pedido.id == info["pedido_id"]).first()
            if pedido:
                pedido.estado = "aceptado"
                pedidos_aceptados.append(str(pedido.id))
        
        db.commit()
        
        # Rechazar la misma asignación (mismo ruta_id) para otros distribuidores
        otras_asignaciones = db.query(AsignacionEntrega).filter(
            AsignacionEntrega.ruta_id == asignacion.ruta_id,
            AsignacionEntrega.id != asignacion.id,
            AsignacionEntrega.estado == "pendiente"
        ).all()
        
        for otra_asignacion in otras_asignaciones:
            otra_asignacion.estado = "rechazada"
        
        db.commit()
        
        return {
            "mensaje": "Asignación aceptada exitosamente",
            "asignacion_id": asignacion.id,
            "estado": asignacion.estado,
            "distribuidor_estado": distribuidor_actual.estado,
            "total_cajas": total_cajas,
            "capacidad_vehiculo": capacidad_vehiculo,
            "pedidos_aceptados": pedidos_aceptados,
            "otras_asignaciones_rechazadas": len(otras_asignaciones)
        }
    
    else:
        # El vehículo NO puede con toda la asignación
        # Necesitamos dividir la asignación
        
        # Primero, aceptar la asignación actual pero solo con lo que cabe
        asignacion.estado = "aceptada"
        
        # Cambiar estado del distribuidor a ocupado
        distribuidor_actual.estado = "ocupado"
        
        # Determinar qué pedidos/entregas puede tomar este distribuidor
        cajas_tomadas = 0
        entregas_tomadas = []
        pedidos_sobrantes = []
        pedidos_tomados = []
        
        for info in pedidos_info:
            if cajas_tomadas + info["cajas"] <= capacidad_vehiculo:
                cajas_tomadas += info["cajas"]
                entregas_tomadas.append(info["entrega_id"])
                pedidos_tomados.append(info["pedido_id"])
            else:
                pedidos_sobrantes.append(info)
        
        # Cambiar estado de los pedidos tomados a "aceptado"
        pedidos_aceptados = []
        for pedido_id in pedidos_tomados:
            pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
            if pedido:
                pedido.estado = "aceptado"
                pedidos_aceptados.append(str(pedido.id))
        
        # Eliminar las entregas que no puede tomar de esta asignación
        for info in pedidos_sobrantes:
            entrega_sobrante = db.query(Entrega).filter(
                Entrega.id_entrega == info["entrega_id"]
            ).first()
            if entrega_sobrante:
                db.delete(entrega_sobrante)
        
        db.commit()
        
        # Rechazar otras asignaciones de la misma ruta para otros distribuidores
        otras_asignaciones = db.query(AsignacionEntrega).filter(
            AsignacionEntrega.ruta_id == asignacion.ruta_id,
            AsignacionEntrega.id != asignacion.id,
            AsignacionEntrega.estado == "pendiente"
        ).all()
        
        for otra_asignacion in otras_asignaciones:
            otra_asignacion.estado = "rechazada"
        
        db.commit()
        
        # Crear nuevas asignaciones para los pedidos sobrantes
        nuevas_asignaciones = _crear_asignacion_para_sobrante(db, pedidos_sobrantes, 10.0)
        
        return {
            "mensaje": "Asignación aceptada parcialmente debido a limitación de capacidad",
            "asignacion_id": asignacion.id,
            "estado": asignacion.estado,
            "distribuidor_estado": distribuidor_actual.estado,
            "total_cajas_originales": total_cajas,
            "cajas_tomadas": cajas_tomadas,
            "capacidad_vehiculo": capacidad_vehiculo,
            "pedidos_aceptados": pedidos_aceptados,
            "pedidos_sobrantes": len(pedidos_sobrantes),
            "otras_asignaciones_rechazadas": len(otras_asignaciones),
            "nuevas_asignaciones_creadas": len(nuevas_asignaciones) if nuevas_asignaciones else 0,
            "nota": f"Se {'crearon nuevas asignaciones' if nuevas_asignaciones else 'intentó crear nuevas asignaciones'} para los pedidos sobrantes"
        }

@router.patch("/asignacion/{asignacion_id}/rechazar", dependencies=[Depends(security)])
def rechazar_asignacion(
    asignacion_id: UUID,
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Permite al distribuidor autenticado rechazar una asignación de entregas.
    """
    # Buscar la asignación
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == asignacion_id,
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=404, 
            detail="Asignación no encontrada o no pertenece a este distribuidor"
        )
    
    # Verificar que esté en estado pendiente
    if asignacion.estado != "pendiente":
        raise HTTPException(
            status_code=400, 
            detail=f"La asignación ya está en estado: {asignacion.estado}"
        )
    
    # Actualizar estado a rechazada
    asignacion.estado = "rechazada"
    db.commit()
    db.refresh(asignacion)
    
    return {
        "mensaje": "Asignación rechazada exitosamente",
        "asignacion_id": asignacion.id,
        "estado": asignacion.estado,
        "fecha_asignacion": asignacion.fecha_asignacion
    }

@router.get("/mis-asignaciones-pendientes", response_model=list[AsignacionEntregaOut], dependencies=[Depends(security)])
def obtener_asignaciones_pendientes(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Obtiene todas las asignaciones pendientes del distribuidor autenticado.
    Solo muestra asignaciones que realmente están disponibles para aceptar.
    """
    # Buscar asignaciones pendientes del distribuidor actual
    asignaciones = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "pendiente"
    ).all()
    
    if not asignaciones:
        return []
    
    # Verificar que no haya asignaciones de la misma ruta ya aceptadas por otros
    asignaciones_validas = []
    for asignacion in asignaciones:
        # Verificar si hay alguna asignación aceptada para la misma ruta
        asignacion_aceptada_existente = db.query(AsignacionEntrega).filter(
            AsignacionEntrega.ruta_id == asignacion.ruta_id,
            AsignacionEntrega.estado == "aceptada",
            AsignacionEntrega.id != asignacion.id
        ).first()
        
        # Si no hay ninguna asignación aceptada para esta ruta, es válida
        if not asignacion_aceptada_existente:
            asignaciones_validas.append(asignacion)
        else:
            # Marcar como rechazada automáticamente si ya fue aceptada por otro
            asignacion.estado = "rechazada"
            db.commit()
    
    # Para cada asignación válida, obtenemos la ruta y las entregas ordenadas
    resultado = []
    for asignacion in asignaciones_validas:
        # Obtener la ruta asociada
        ruta = db.query(RutaEntrega).filter(
            RutaEntrega.ruta_id == asignacion.ruta_id
        ).first()
        
        if ruta:
            # Obtener las entregas ordenadas por orden_entrega
            entregas_ordenadas = db.query(Entrega).filter(
                Entrega.asignacion_id == asignacion.id
            ).order_by(Entrega.orden_entrega).all()
            
            # Construir el objeto de respuesta
            asignacion_data = {
                "id": asignacion.id,
                "fecha_asignacion": asignacion.fecha_asignacion,
                "estado": asignacion.estado,
                "ruta": {
                    "ruta_id": ruta.ruta_id,
                    "coordenadas_inicio": ruta.coordenadas_inicio,
                    "coordenadas_fin": ruta.coordenadas_fin,
                    "distancia": float(ruta.distancia) if ruta.distancia else None,
                    "tiempo_estimado": ruta.tiempo_estimado,
                    "entregas": [
                        {
                            "id_entrega": entrega.id_entrega,
                            "fecha_hora_reg": entrega.fecha_hora_reg,
                            "coordenadas_fin": entrega.coordenadas_fin,
                            "estado": entrega.estado,
                            "observaciones": entrega.observaciones,
                            "orden_entrega": entrega.orden_entrega,
                            "cliente": entrega.cliente,
                            "pedido": entrega.pedido
                        }
                        for entrega in entregas_ordenadas
                    ]
                }
            }
            resultado.append(asignacion_data)
    
    return resultado

@router.get("/mi-capacidad-vehiculo", dependencies=[Depends(security)])
def obtener_capacidad_vehiculo(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Obtiene información sobre el vehículo y capacidad del distribuidor autenticado.
    """
    from app.models.asignacion_vehiculo_model import AsignacionVehiculo
    from app.models.vehiculo_model import Vehiculo
    
    # Obtener el vehículo del distribuidor
    vehiculo_asignado = db.query(AsignacionVehiculo).filter(
        AsignacionVehiculo.id_distribuidor == distribuidor_actual.id
    ).first()
    
    if not vehiculo_asignado:
        return {
            "tiene_vehiculo": False,
            "mensaje": "No tienes un vehículo asignado"
        }
    
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id == vehiculo_asignado.id_vehiculo
    ).first()
    
    if not vehiculo:
        return {
            "tiene_vehiculo": False,
            "mensaje": "Vehículo no encontrado"
        }
    
    return {
        "tiene_vehiculo": True,
        "vehiculo": {
            "id": vehiculo.id,
            "marca": vehiculo.marca,
            "modelo": vehiculo.modelo,
            "placa": vehiculo.placa,
            "capacidad_carga": vehiculo.capacidad_carga,
            "tipo_vehiculo": vehiculo.tipo_vehiculo,
            "anio": vehiculo.anio
        },
        "mensaje": f"Puedes transportar hasta {vehiculo.capacidad_carga} cajas"
    }

@router.get("/verificar-estado-asignacion/{asignacion_id}", dependencies=[Depends(security)])
def verificar_estado_asignacion(
    asignacion_id: UUID,
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Verifica el estado actual de una asignación antes de que el distribuidor intente aceptarla.
    Útil para evitar que distribuidores intenten aceptar asignaciones ya tomadas.
    """
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == asignacion_id
    ).first()
    
    if not asignacion:
        raise HTTPException(
            status_code=404,
            detail="Asignación no encontrada"
        )
    
    # Verificar si la asignación pertenece al distribuidor actual
    es_propia = asignacion.id_distribuidor == distribuidor_actual.id
    
    return {
        "asignacion_id": asignacion_id,
        "estado": asignacion.estado,
        "es_propia": es_propia,
        "puede_aceptar": asignacion.estado == "pendiente" and es_propia,
        "fecha_asignacion": asignacion.fecha_asignacion,
        "mensaje": _obtener_mensaje_estado(asignacion.estado, es_propia)
    }

def _obtener_mensaje_estado(estado: str, es_propia: bool) -> str:
    """Obtiene un mensaje descriptivo basado en el estado de la asignación"""
    if estado == "pendiente":
        return "Asignación disponible para aceptar" if es_propia else "Esta asignación está pendiente para otro distribuidor"
    elif estado == "aceptada":
        return "Ya aceptaste esta asignación" if es_propia else "Esta asignación ya fue aceptada por otro distribuidor"
    elif estado == "rechazada":
        return "Asignación rechazada"
    else:
        return f"Estado desconocido: {estado}"

def _crear_asignacion_para_sobrante(db: Session, pedidos_sobrantes: list, radio_maximo_km: float = 10.0):
    """
    Crea una nueva asignación para los pedidos sobrantes usando distribuidores cercanos.
    Incluye verificación de asignaciones duplicadas.
    """
    from app.services.asignacion_service import _obtener_distribuidores_cercanos, verificar_asignacion_duplicada
    
    if not pedidos_sobrantes:
        return None
    
    # Verificar si hay asignaciones duplicadas para estos pedidos
    pedidos_ids = [info["pedido_id"] for info in pedidos_sobrantes]
    es_duplicada, mensaje = verificar_asignacion_duplicada(db, pedidos_ids=pedidos_ids)
    if es_duplicada:
        print(f"⚠️ Asignación duplicada detectada para pedidos sobrantes: {mensaje}")
        return None
    
    # Obtener información de los pedidos sobrantes
    pedidos_validos = []
    for info in pedidos_sobrantes:
        pedido = db.query(Pedido).filter(Pedido.id == info["pedido_id"]).first()
        if pedido:
            cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
            if cliente and cliente.coordenadas:
                try:
                    lat, lon = map(float, cliente.coordenadas.split(","))
                    pedidos_validos.append((pedido, cliente, (lat, lon)))
                except (ValueError, TypeError):
                    continue
    
    if not pedidos_validos:
        return None
    
    # Calcular punto central de los pedidos sobrantes
    centro_lat = sum(coord[2][0] for coord in pedidos_validos) / len(pedidos_validos)
    centro_lon = sum(coord[2][1] for coord in pedidos_validos) / len(pedidos_validos)
    punto_central = (centro_lat, centro_lon)
    
    # Buscar distribuidores cercanos al punto central
    distribuidores_disponibles = _obtener_distribuidores_cercanos(db, punto_central, radio_maximo_km)
    if not distribuidores_disponibles:
        return None
    
    # Crear asignaciones para múltiples distribuidores si es necesario
    asignaciones_creadas = []
    pedidos_pendientes = pedidos_validos.copy()
    
    for dist_info in distribuidores_disponibles:
        if not pedidos_pendientes:
            break
            
        distribuidor = dist_info["distribuidor"]
        vehiculo = dist_info["vehiculo"]
        capacidad = vehiculo.capacidad_carga
        
        # Tomar hasta la capacidad del vehículo
        pedidos_para_este_distribuidor = []
        cajas_asignadas = 0
        
        for i, (pedido, cliente, coords) in enumerate(pedidos_pendientes):
            # Contar cajas del pedido
            detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido.id).all()
            cajas_pedido = sum(detalle.cantidad for detalle in detalles)
            
            if cajas_asignadas + cajas_pedido <= capacidad:
                pedidos_para_este_distribuidor.append((pedido, cliente, coords))
                cajas_asignadas += cajas_pedido
        
        if not pedidos_para_este_distribuidor:
            continue
        
        # Remover pedidos asignados de la lista pendiente
        for pedido_asignado in pedidos_para_este_distribuidor:
            if pedido_asignado in pedidos_pendientes:
                pedidos_pendientes.remove(pedido_asignado)
        
        # Crear ruta simple sin optimización avanzada
        tiendas = db.query(Tienda).filter(
            Tienda.latitud.isnot(None), 
            Tienda.longitud.isnot(None)
        ).all()
        
        if not tiendas:
            continue
            
        tienda_inicial = min(tiendas, key=lambda t: geodesic(
            (distribuidor.latitud, distribuidor.longitud),
            (t.latitud, t.longitud)
        ).km)
        
        # Crear ruta simple
        coords_inicio = f"{tienda_inicial.latitud},{tienda_inicial.longitud}"
        coords_fin = pedidos_para_este_distribuidor[-1][1].coordenadas
        
        ruta = RutaEntrega(
            coordenadas_inicio=coords_inicio,
            coordenadas_fin=coords_fin,
            distancia=0.0,  # Se puede calcular después
            tiempo_estimado="Sin calcular"
        )
        
        db.add(ruta)
        db.commit()
        db.refresh(ruta)
        
        # Crear asignación para cada distribuidor cercano (competencia)
        distribuidores_para_competir = distribuidores_disponibles[:3]  # Los 3 más cercanos
        
        for competidor_info in distribuidores_para_competir:
            nueva_asignacion = AsignacionEntrega(
                id_distribuidor=competidor_info["distribuidor"].id,
                ruta_id=ruta.ruta_id,
                estado="pendiente"
            )
            db.add(nueva_asignacion)
            db.commit()
            db.refresh(nueva_asignacion)
            
            # Optimizar orden de entregas usando la tienda como punto de inicio
            pedidos_optimizados = _optimizar_orden_entregas_sobrantes(
                pedidos_para_este_distribuidor,
                (tienda_inicial.latitud, tienda_inicial.longitud)
            )
            
            # Crear entregas para cada pedido con orden optimizado
            for orden, (pedido, cliente, coords) in enumerate(pedidos_optimizados, 1):
                entrega = Entrega(
                    ruta_id=ruta.ruta_id,
                    cliente_id=cliente.id,
                    pedido_id=pedido.id,
                    asignacion_id=nueva_asignacion.id,
                    coordenadas_fin=cliente.coordenadas,
                    orden_entrega=orden
                )
                db.add(entrega)
            
            # Agregar a pedidos asignados
            for pedido, _, _ in pedidos_para_este_distribuidor:
                pedido_asignado = PedidoAsignado(
                    pedido_id=pedido.id,
                    asignacion_id=nueva_asignacion.id
                )
                db.add(pedido_asignado)
            
            asignaciones_creadas.append(nueva_asignacion)
        
        db.commit()
        break  # Solo crear una ruta por ahora
    
    return asignaciones_creadas

@router.post("/limpiar-asignaciones-obsoletas", dependencies=[Depends(security)])
def limpiar_asignaciones_obsoletas(
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db),
    horas_limite: int = 24
):
    """
    Limpia asignaciones pendientes obsoletas (más antiguas que el límite especificado).
    Solo afecta las asignaciones del distribuidor autenticado.
    """
    from datetime import datetime, timedelta
    
    tiempo_limite = datetime.utcnow() - timedelta(hours=horas_limite)
    
    # Buscar asignaciones pendientes obsoletas del distribuidor actual
    asignaciones_obsoletas = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "pendiente",
        AsignacionEntrega.fecha_asignacion < tiempo_limite
    ).all()
    
    if not asignaciones_obsoletas:
        return {
            "mensaje": "No hay asignaciones obsoletas para limpiar",
            "asignaciones_limpiadas": 0,
            "limite_horas": horas_limite
        }
    
    # Marcar como rechazadas
    for asignacion in asignaciones_obsoletas:
        asignacion.estado = "rechazada"
    
    db.commit()
    
    return {
        "mensaje": f"Se limpiaron {len(asignaciones_obsoletas)} asignaciones obsoletas",
        "asignaciones_limpiadas": len(asignaciones_obsoletas),
        "limite_horas": horas_limite,
        "asignaciones_ids": [str(a.id) for a in asignaciones_obsoletas]
    }

@router.patch("/completar/{entrega_id}", dependencies=[Depends(security)])
def marcar_entrega_completada(
    entrega_id: UUID,
    datos_entrega: EntregaUpdate,
    distribuidor_actual: Distribuidor = Depends(get_current_distribuidor),
    db: Session = Depends(get_db)
):
    """
    Marca una entrega como completada/fallida, actualiza el estado del pedido y guarda 
    las coordenadas finales y observaciones.
    """
    # Buscar la entrega
    entrega = db.query(Entrega).join(AsignacionEntrega).filter(
        Entrega.id_entrega == entrega_id,
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id
    ).first()
    
    if not entrega:
        raise HTTPException(
            status_code=404,
            detail="Entrega no encontrada o no pertenece a este distribuidor"
        )
    
    if entrega.estado in ["entregado", "fallido"]:
        return {
            "mensaje": f"La entrega ya está marcada como {entrega.estado}",
            "entrega_id": entrega_id,
            "estado": entrega.estado
        }
    
    # Actualizar la entrega con los datos recibidos
    entrega.estado = datos_entrega.estado
    entrega.coordenadas_fin = datos_entrega.coordenadas_fin
    entrega.observaciones = datos_entrega.observaciones
    
    # Actualizar estado del pedido según el resultado de la entrega
    estado_pedido = None
    if entrega.pedido_id:
        pedido = db.query(Pedido).filter(Pedido.id == entrega.pedido_id).first()
        if pedido:
            if datos_entrega.estado == "entregado":
                pedido.estado = "entregado"
                estado_pedido = "entregado"
            elif datos_entrega.estado == "fallido":
                pedido.estado = "fallido"
                estado_pedido = "fallido"
    
    db.commit()
    
    entregas_reoptimizadas = False
    ruta_actualizada = False
    nuevas_coordenadas_inicio = None
    
    if datos_entrega.estado == "entregado" and datos_entrega.coordenadas_fin:
        try:
            lat, lon = map(float, datos_entrega.coordenadas_fin.split(","))
            ultima_ubicacion = (lat, lon)
            _reoptimizar_entregas_pendientes(db, distribuidor_actual.id, ultima_ubicacion)
            entregas_reoptimizadas = True
            
            ruta = db.query(RutaEntrega).filter(
                RutaEntrega.ruta_id == entrega.ruta_id
            ).first()
            
            if ruta:
                ruta.coordenadas_inicio = datos_entrega.coordenadas_fin
                nuevas_coordenadas_inicio = datos_entrega.coordenadas_fin
                ruta_actualizada = True
                db.commit()
                
        except (ValueError, TypeError):
            pass
    
    entregas_pendientes = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_actual.id,
        AsignacionEntrega.estado == "aceptada",
        Entrega.estado == "pendiente"
    ).count()
    
    estado_distribuidor_actualizado = False
    if entregas_pendientes == 0 and distribuidor_actual.estado == "ocupado":
        distribuidor_actual.estado = "disponible"
        estado_distribuidor_actualizado = True
        db.commit()
    
    return {
        "mensaje": f"Entrega marcada como {datos_entrega.estado} exitosamente",
        "entrega_id": entrega_id,
        "pedido_id": entrega.pedido_id,
        "estado_entrega": entrega.estado,
        "estado_pedido": estado_pedido,
        "coordenadas_fin": entrega.coordenadas_fin,
        "observaciones": entrega.observaciones,
        "distribuidor_estado": distribuidor_actual.estado,
        "todas_entregas_completadas": entregas_pendientes == 0,
        "estado_distribuidor_actualizado": estado_distribuidor_actualizado,
        "entregas_reoptimizadas": entregas_reoptimizadas,
        "ruta_actualizada": ruta_actualizada,
        "nuevas_coordenadas_inicio": nuevas_coordenadas_inicio
    }

def _optimizar_orden_entregas(db: Session, pedidos_asignados: list, punto_inicio: tuple):
    """
    Optimiza el orden de entregas usando el algoritmo del vecino más cercano.
    
    Args:
        db: Sesión de base de datos
        pedidos_asignados: Lista de pedidos asignados
        punto_inicio: Tupla (lat, lon) del punto de inicio (tienda donde se recogen los productos)
    
    Returns:
        Lista de pedidos ordenados por ruta óptima
    """
    # Obtener información de ubicación de cada pedido
    pedidos_con_ubicacion = []
    for pedido_asignado in pedidos_asignados:
        pedido = db.query(Pedido).filter(Pedido.id == pedido_asignado.pedido_id).first()
        if pedido:
            cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_id).first()
            if cliente and cliente.coordenadas:
                try:
                    lat, lon = map(float, cliente.coordenadas.split(","))
                    pedidos_con_ubicacion.append({
                        'pedido_asignado': pedido_asignado,
                        'pedido': pedido,
                        'cliente': cliente,
                        'coordenadas': (lat, lon)
                    })
                except (ValueError, TypeError):
                    # Si hay error en coordenadas, agregar al final
                    pedidos_con_ubicacion.append({
                        'pedido_asignado': pedido_asignado,
                        'pedido': pedido,
                        'cliente': cliente,
                        'coordenadas': None
                    })
    
    if not pedidos_con_ubicacion:
        return pedidos_asignados
    
    # Separar pedidos con y sin coordenadas válidas
    pedidos_con_coords = [p for p in pedidos_con_ubicacion if p['coordenadas'] is not None]
    pedidos_sin_coords = [p for p in pedidos_con_ubicacion if p['coordenadas'] is None]
    
    if not pedidos_con_coords:
        return pedidos_asignados
    
    # Algoritmo del vecino más cercano
    ruta_optimizada = []
    pedidos_restantes = pedidos_con_coords.copy()
    ubicacion_actual = punto_inicio
    
    while pedidos_restantes:
        # Encontrar el pedido más cercano a la ubicación actual
        pedido_mas_cercano = None
        distancia_minima = float('inf')
        
        for pedido_info in pedidos_restantes:
            distancia = geodesic(ubicacion_actual, pedido_info['coordenadas']).km
            if distancia < distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido_info
        
        if pedido_mas_cercano:
            # Agregar a la ruta optimizada y actualizar ubicación actual
            ruta_optimizada.append(pedido_mas_cercano)
            ubicacion_actual = pedido_mas_cercano['coordenadas']
            pedidos_restantes.remove(pedido_mas_cercano)
    
    # Agregar pedidos sin coordenadas al final
    ruta_optimizada.extend(pedidos_sin_coords)
    
    # Retornar solo los pedidos_asignados en el orden optimizado
    return [info['pedido_asignado'] for info in ruta_optimizada]

def _optimizar_orden_entregas_sobrantes(pedidos_info: list, punto_inicio: tuple):
    """
    Optimiza el orden de entregas para pedidos sobrantes usando el algoritmo del vecino más cercano.
    
    Args:
        pedidos_info: Lista de tuplas (pedido, cliente, coordenadas)
        punto_inicio: Tupla (lat, lon) del punto de inicio (tienda)
    
    Returns:
        Lista de tuplas ordenadas por ruta óptima
    """
    if not pedidos_info:
        return []
    
    # Separar pedidos con y sin coordenadas válidas
    pedidos_con_coords = [p for p in pedidos_info if p[2] is not None]
    pedidos_sin_coords = [p for p in pedidos_info if p[2] is None]
    
    if not pedidos_con_coords:
        return pedidos_info
    
    # Algoritmo del vecino más cercano
    ruta_optimizada = []
    pedidos_restantes = pedidos_con_coords.copy()
    ubicacion_actual = punto_inicio
    
    while pedidos_restantes:
        # Encontrar el pedido más cercano a la ubicación actual
        pedido_mas_cercano = None
        distancia_minima = float('inf')
        
        for pedido_info in pedidos_restantes:
            distancia = geodesic(ubicacion_actual, pedido_info[2]).km
            if distancia < distancia_minima:
                distancia_minima = distancia
                pedido_mas_cercano = pedido_info
        
        if pedido_mas_cercano:
            # Agregar a la ruta optimizada y actualizar ubicación actual
            ruta_optimizada.append(pedido_mas_cercano)
            ubicacion_actual = pedido_mas_cercano[2]
            pedidos_restantes.remove(pedido_mas_cercano)
    
    # Agregar pedidos sin coordenadas al final
    ruta_optimizada.extend(pedidos_sin_coords)
    
    return ruta_optimizada

def _reoptimizar_entregas_pendientes(db: Session, distribuidor_id: UUID, ultima_ubicacion: tuple):
    """
    Reoptimiza las entregas pendientes del distribuidor basándose en su ubicación actual.
    
    Args:
        db: Sesión de base de datos
        distribuidor_id: ID del distribuidor
        ultima_ubicacion: Tupla (lat, lon) de la última ubicación conocida
    """
    # Obtener entregas pendientes del distribuidor ordenadas por orden_entrega
    entregas_pendientes = db.query(Entrega).join(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_id,
        AsignacionEntrega.estado == "aceptada",
        Entrega.estado == "pendiente"
    ).order_by(Entrega.orden_entrega).all()
    
    if len(entregas_pendientes) <= 1:
        # Si hay 1 o menos entregas pendientes, no hay nada que optimizar
        return
    
    # Convertir entregas a formato para optimización
    entregas_info = []
    for entrega in entregas_pendientes:
        if entrega.coordenadas_fin:
            try:
                lat, lon = map(float, entrega.coordenadas_fin.split(","))
                entregas_info.append({
                    'entrega': entrega,
                    'coordenadas': (lat, lon)
                })
            except (ValueError, TypeError):
                # Si hay error en coordenadas, mantener al final
                entregas_info.append({
                    'entrega': entrega,
                    'coordenadas': None
                })
    
    if len(entregas_info) <= 1:
        return
    
    # Aplicar algoritmo del vecino más cercano desde la ubicación actual
    entregas_con_coords = [e for e in entregas_info if e['coordenadas'] is not None]
    entregas_sin_coords = [e for e in entregas_info if e['coordenadas'] is None]
    
    if not entregas_con_coords:
        return
    
    # Algoritmo del vecino más cercano
    ruta_optimizada = []
    entregas_restantes = entregas_con_coords.copy()
    ubicacion_actual = ultima_ubicacion
    
    while entregas_restantes:
        # Encontrar la entrega más cercana a la ubicación actual
        entrega_mas_cercana = None
        distancia_minima = float('inf')
        
        for entrega_info in entregas_restantes:
            distancia = geodesic(ubicacion_actual, entrega_info['coordenadas']).km
            if distancia < distancia_minima:
                distancia_minima = distancia
                entrega_mas_cercana = entrega_info
        
        if entrega_mas_cercana:
            # Agregar a la ruta optimizada y actualizar ubicación actual
            ruta_optimizada.append(entrega_mas_cercana)
            ubicacion_actual = entrega_mas_cercana['coordenadas']
            entregas_restantes.remove(entrega_mas_cercana)
    
    # Agregar entregas sin coordenadas al final
    ruta_optimizada.extend(entregas_sin_coords)
    
    # Actualizar el orden_entrega en la base de datos
    for nuevo_orden, entrega_info in enumerate(ruta_optimizada, 1):
        entrega_info['entrega'].orden_entrega = nuevo_orden
    
    db.commit()
    
    print(f"✅ Reoptimizadas {len(ruta_optimizada)} entregas pendientes para distribuidor {distribuidor_id}")
