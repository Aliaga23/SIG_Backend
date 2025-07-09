from sqlalchemy.orm import Session
from uuid import UUID
from app.models.asignacion_model import AsignacionEntrega, PedidoAsignado
from app.schemas.asignacion_schema import AsignacionEntregaCreate, PedidoAsignadoCreate
from geopy.distance import geodesic
from app.models.cliente_model import Cliente
from app.models.pedido_model import Pedido, DetallePedido
from app.models.vehiculo_model import Vehiculo
from app.models.asignacion_vehiculo_model import AsignacionVehiculo
from app.models.ruta_entrega_model import RutaEntrega, Entrega
from app.models.distribuidor_model import Distribuidor
from app.models.tienda_model import Tienda
from app.models.producto_model import Producto

def crear_asignacion_entrega(db: Session, datos: AsignacionEntregaCreate):
    nueva = AsignacionEntrega(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

def listar_asignaciones(db: Session):
    return db.query(AsignacionEntrega).all()

def obtener_asignacion(db: Session, asignacion_id: UUID):
    return db.query(AsignacionEntrega).filter(AsignacionEntrega.id == asignacion_id).first()

def eliminar_asignacion(db: Session, asignacion_id: UUID):
    asignacion = obtener_asignacion(db, asignacion_id)
    if asignacion:
        db.delete(asignacion)
        db.commit()
    return asignacion


def asignar_pedido_a_entrega(db: Session, datos: PedidoAsignadoCreate):
    asignacion = PedidoAsignado(**datos.dict())
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)
    return asignacion

def listar_pedidos_asignados_por_asignacion(db: Session, asignacion_id: UUID):
    return db.query(PedidoAsignado).filter(PedidoAsignado.asignacion_id == asignacion_id).all()

def eliminar_pedido_asignado(db: Session, pedido_asignado_id: UUID):
    pa = db.query(PedidoAsignado).filter(PedidoAsignado.id == pedido_asignado_id).first()
    if pa:
        db.delete(pa)
        db.commit()
    return pa

def asignacion_automatica_propuesta(db: Session, pedidos_ids: list[UUID] = None, radio_maximo_km: float = 5.0):
    """
    Genera una propuesta de asignación automática buscando el distribuidor más cercano.
    Si no se especifican pedidos, toma todos los pedidos pendientes.
    El distribuidor asignado puede aceptar o rechazar.
    Si hay más pedidos que la capacidad del vehículo, se crean múltiples asignaciones.
    """
    if pedidos_ids:
        pedidos_pendientes = db.query(Pedido).filter(
            Pedido.id.in_(pedidos_ids),
            Pedido.estado == "pendiente"
        ).all()
    else:
        pedidos_pendientes = db.query(Pedido).filter_by(estado="pendiente").all()
    
    if not pedidos_pendientes:
        raise ValueError("No hay pedidos pendientes para asignar")

    # 2. Filtrar pedidos con coordenadas válidas
    pedidos_validos = []
    for pedido in pedidos_pendientes:
        cliente = db.query(Cliente).filter_by(id=pedido.cliente_id).first()
        if cliente and cliente.coordenadas:
            try:
                lat, lon = map(float, cliente.coordenadas.split(","))
                pedidos_validos.append((pedido, cliente, (lat, lon)))
            except (ValueError, TypeError):
                continue
    
    if not pedidos_validos:
        raise ValueError("No hay pedidos con coordenadas válidas")
    
    # 3. Calcular punto central
    centro_lat = sum(coord[2][0] for coord in pedidos_validos) / len(pedidos_validos)
    centro_lon = sum(coord[2][1] for coord in pedidos_validos) / len(pedidos_validos)
    punto_central = (centro_lat, centro_lon)
    
    # 4. Seleccionar distribuidor y inicializar ruta desde tienda
    distribuidores_disponibles = _obtener_distribuidores_cercanos(db, punto_central, radio_maximo_km * 2)
    if not distribuidores_disponibles:
        raise ValueError("No hay distribuidores disponibles en el área")
    distribuidores_disponibles.sort(key=lambda x: x["distancia_km"])
    distribuidor_asignado = distribuidores_disponibles[0]["distribuidor"]
    vehiculo_asignado = distribuidores_disponibles[0]["vehiculo"]
    # Ubicación inicial: tienda más cercana al distribuidor
    tiendas = db.query(Tienda).filter(
        Tienda.latitud.isnot(None), Tienda.longitud.isnot(None)
    ).all()
    if not tiendas:
        raise ValueError("No hay tiendas con coordenadas registradas")
    tienda_inicial = min(tiendas, key=lambda t: geodesic(
        (distribuidor_asignado.latitud, distribuidor_asignado.longitud),
        (t.latitud, t.longitud)
    ).km)
    current_start = (tienda_inicial.latitud, tienda_inicial.longitud)
    
    # 5. Crear una sola asignación con todos los pedidos
    cluster_seleccionado = pedidos_validos  # todos los pedidos válidos
    coords_cluster = [item[2] for item in cluster_seleccionado]
    clientes_cluster = [item[1] for item in cluster_seleccionado]
    ruta = _calcular_ruta_optimizada(
        current_start,
        coords_cluster,
        tienda_inicial,
        clientes_cluster
    )
    db.add(ruta); db.commit(); db.refresh(ruta)
    nueva_asignacion = AsignacionEntrega(
        id_distribuidor=distribuidor_asignado.id,
        ruta_id=ruta.ruta_id,
        estado="pendiente"
    )
    db.add(nueva_asignacion); db.commit(); db.refresh(nueva_asignacion)
    for pedido, _, _ in cluster_seleccionado:
        db.add(PedidoAsignado(pedido_id=pedido.id, asignacion_id=nueva_asignacion.id))
    db.commit()
    asignaciones_creadas = [nueva_asignacion]
    
    if not asignaciones_creadas:
        raise ValueError("No se pudo crear ninguna asignación con los criterios establecidos")
    
    return asignaciones_creadas

def _obtener_distribuidores_cercanos(db: Session, punto_central: tuple, radio_maximo_km: float):
    """
    Obtiene distribuidores disponibles ordenados por proximidad a un punto central.
    """
    # Obtener distribuidores activos con coordenadas
    distribuidores = db.query(Distribuidor).filter(
        Distribuidor.activo == True,
        Distribuidor.latitud.isnot(None),
        Distribuidor.longitud.isnot(None)
    ).all()
    
    distribuidores_disponibles = []
    
    for distribuidor in distribuidores:
        # Verificar que tenga vehículo asignado
        asignacion_vehiculo = db.query(AsignacionVehiculo).filter_by(
            id_distribuidor=distribuidor.id
        ).first()
        
        if not asignacion_vehiculo:
            continue
        
        vehiculo = db.query(Vehiculo).filter_by(id=asignacion_vehiculo.id_vehiculo).first()
        if not vehiculo:
            continue
        
        # Calcular distancia al punto central
        distancia = geodesic(
            (distribuidor.latitud, distribuidor.longitud),
            punto_central
        ).km
        
        # Filtrar por radio máximo
        if distancia <= radio_maximo_km:
            distribuidores_disponibles.append({
                "distribuidor": distribuidor,
                "vehiculo": vehiculo,
                "distancia_km": round(distancia, 2),
                "capacidad_pedidos": vehiculo.capacidad_carga
            })
    
    # Ordenar por distancia (más cercano primero)
    distribuidores_disponibles.sort(key=lambda x: x["distancia_km"])
    
    return distribuidores_disponibles

def _encontrar_cluster_cercano(pedidos_coords, centro_distribuidor, radio_max, capacidad_max):
    """Encuentra un cluster de pedidos cercanos al distribuidor"""
    if not pedidos_coords:
        return []
    
    # Ordenar pedidos por distancia al distribuidor
    pedidos_ordenados = sorted(pedidos_coords, key=lambda x: geodesic(
        centro_distribuidor, x[2]
    ).km)
    
    cluster = []
    for pedido, cliente, coords in pedidos_ordenados:
        if len(cluster) >= capacidad_max:
            break
        
        # Verificar si el pedido está dentro del radio máximo respecto al distribuidor
        distancia_a_distribuidor = geodesic(centro_distribuidor, coords).km
        if distancia_a_distribuidor > radio_max:
            continue
        
        # Verificar si el pedido está cerca de los otros pedidos del cluster
        if not cluster:
            cluster.append((pedido, cliente, coords))
        else:
            # Verificar distancia promedio a otros pedidos del cluster
            distancias = [geodesic(coords, c[2]).km for c in cluster]
            distancia_promedio = sum(distancias) / len(distancias)
            
            if distancia_promedio <= radio_max:
                cluster.append((pedido, cliente, coords))
    
    return cluster

def _calcular_ruta_optimizada(coords_tienda, coords_clientes, tienda, clientes):
    """Calcula una ruta optimizada usando Google Maps API o algoritmo del vecino más cercano"""
    from app.services.maps_service import calcular_ruta_multiple, obtener_distancia_tiempo
    
    if not coords_clientes:
        raise ValueError("No hay coordenadas de clientes")
    
    # Intentar usar Google Maps API para ruta optimizada
    ruta_google = calcular_ruta_multiple(coords_tienda, coords_clientes)
    
    if ruta_google:
        # Si tenemos resultado de Google Maps, usarlo
        coord_inicio = f"{coords_tienda[0]},{coords_tienda[1]}"
        coord_fin = f"{coords_clientes[-1][0]},{coords_clientes[-1][1]}" if coords_clientes else coord_inicio
        
        return RutaEntrega(
            coordenadas_inicio=coord_inicio,
            coordenadas_fin=coord_fin,
            distancia=ruta_google["distancia_km"],
            tiempo_estimado=ruta_google["tiempo_estimado"]
        )
    
    # Algoritmo de respaldo: vecino más cercano
    ruta_ordenada = []
    coords_disponibles = coords_clientes.copy()
    clientes_disponibles = clientes.copy()
    punto_actual = coords_tienda
    
    while coords_disponibles:
        # Encontrar el cliente más cercano
        idx_cercano = min(range(len(coords_disponibles)), 
                         key=lambda i: geodesic(punto_actual, coords_disponibles[i]).km)
        
        coords_cercanas = coords_disponibles.pop(idx_cercano)
        cliente_cercano = clientes_disponibles.pop(idx_cercano)
        
        ruta_ordenada.append((coords_cercanas, cliente_cercano))
        punto_actual = coords_cercanas
    
    # Calcular distancia y tiempo usando la API de Google Maps
    distancia_total = 0
    tiempo_total = 0
    
    # De tienda al primer cliente
    if ruta_ordenada:
        distancia, tiempo = obtener_distancia_tiempo(
            coords_tienda, ruta_ordenada[0][0]
        )
        distancia_total += distancia
        # Convertir tiempo a minutos si viene como string
        if isinstance(tiempo, str) and "mins" in tiempo:
            tiempo_total += int(tiempo.split()[0])
    
    # Entre clientes consecutivos
    for i in range(len(ruta_ordenada) - 1):
        distancia, tiempo = obtener_distancia_tiempo(
            ruta_ordenada[i][0], ruta_ordenada[i+1][0]
        )
        distancia_total += distancia
        # Convertir tiempo a minutos si viene como string
        if isinstance(tiempo, str) and "mins" in tiempo:
            tiempo_total += int(tiempo.split()[0])
    
    # Crear objeto RutaEntrega
    coord_inicio = f"{coords_tienda[0]},{coords_tienda[1]}"
    coord_fin = f"{ruta_ordenada[-1][0][0]},{ruta_ordenada[-1][0][1]}" if ruta_ordenada else coord_inicio
    
    return RutaEntrega(
        coordenadas_inicio=coord_inicio,
        coordenadas_fin=coord_fin,
        distancia=distancia_total,
        tiempo_estimado=f"{tiempo_total} mins" if tiempo_total > 0 else f"{int(distancia_total * 2.5)} mins"
    )

def aceptar_asignacion(db: Session, asignacion_id: UUID, distribuidor_id: UUID):
    """El distribuidor acepta una asignación pendiente"""
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == asignacion_id,
        AsignacionEntrega.id_distribuidor == distribuidor_id,
        AsignacionEntrega.estado == "pendiente"
    ).first()
    
    if not asignacion:
        raise ValueError("Asignación no encontrada o ya procesada")
    
    # Cambiar estado de la asignación
    asignacion.estado = "aceptada"
    
    # Cambiar estado de los pedidos asignados
    pedidos_asignados = db.query(PedidoAsignado).filter_by(asignacion_id=asignacion_id).all()
    for pedido_asignado in pedidos_asignados:
        pedido = db.query(Pedido).filter_by(id=pedido_asignado.pedido_id).first()
        if pedido:
            pedido.estado = "asignado"
    
    # Crear paradas de entrega para cada pedido asignado
    for index, pedido_as in enumerate(pedidos_asignados, start=1):
        pedido = db.query(Pedido).filter(Pedido.id == pedido_as.pedido_id).first()
        if not pedido:
            continue
        # Evitar duplicados si ya existe la entrega para este pedido
        existing = db.query(Entrega).filter(Entrega.pedido_id == pedido.id).first()
        if existing:
            continue
        entrega = Entrega(
            ruta_id=asignacion.ruta_id,
            cliente_id=pedido.cliente_id,
            pedido_id=pedido.id,
            orden_entrega=index,
            estado="en_ruta",
            asignacion_id=asignacion.id
        )
        db.add(entrega)
    
    db.commit()
    db.refresh(asignacion)
    return asignacion

def rechazar_asignacion(db: Session, asignacion_id: UUID, distribuidor_id: UUID):
    """El distribuidor rechaza una asignación pendiente"""
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == asignacion_id,
        AsignacionEntrega.id_distribuidor == distribuidor_id,
        AsignacionEntrega.estado == "pendiente"
    ).first()
    
    if not asignacion:
        raise ValueError("Asignación no encontrada o ya procesada")
    
    # Cambiar estado de la asignación
    asignacion.estado = "rechazada"
    
    # Los pedidos permanecen en estado "pendiente" para ser reasignados
    
    db.commit()
    db.refresh(asignacion)
    return asignacion

def listar_asignaciones_pendientes(db: Session, distribuidor_id: UUID):
    """Lista las asignaciones pendientes para un distribuidor"""
    return db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id_distribuidor == distribuidor_id,
        AsignacionEntrega.estado == "pendiente"
    ).all()