from sqlalchemy.orm import Session
from uuid import UUID
from app.models.asignacion_model import AsignacionEntrega, PedidoAsignado
from app.schemas.asignacion_schema import AsignacionEntregaCreate, PedidoAsignadoCreate
from geopy.distance import geodesic
from app.models.cliente_model import Cliente
from app.models.pedido_model import Pedido
from app.models.vehiculo_model import Vehiculo
from app.models.asignacion_vehiculo_model import AsignacionVehiculo
from app.models.ruta_entrega_model import RutaEntrega

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

def asignacion_automatica(db: Session, distribuidor_id: UUID):
    # 1. Obtener vehículo del distribuidor
    asignacion = db.query(AsignacionVehiculo).filter_by(id_distribuidor=distribuidor_id).first()
    if not asignacion:
        raise ValueError("Distribuidor no tiene vehículo asignado")

    vehiculo = db.query(Vehiculo).filter_by(id=asignacion.id_vehiculo).first()
    capacidad_restante = vehiculo.capacidad_carga

    # 2. Obtener pedidos no asignados y pendientes
    pedidos_pendientes = db.query(Pedido).filter_by(estado="pendiente").all()

    # 3. Ordenar por cercanía
    def distancia_pedido(pedido):
        cliente = db.query(Cliente).filter_by(id=pedido.cliente_id).first()
        if cliente and cliente.coordenadas:
            latlon = tuple(map(float, cliente.coordenadas.split(",")))
            # se puede reemplazar con ubicación real del distribuidor
            origen = (-17.783, -63.182)  # Santa Cruz centro
            return geodesic(origen, latlon).km
        return float("inf")

    pedidos_ordenados = sorted(pedidos_pendientes, key=distancia_pedido)

    # 4. Asignar pedidos dentro de la capacidad
    asignados = []
    for pedido in pedidos_ordenados:
        if capacidad_restante <= 0:
            break
        asignados.append(pedido)
        capacidad_restante -= 1  # se puede ajustar a unidades o peso , Bulacia hizo la base ya no se puede cambiar

    if not asignados:
        raise ValueError("No hay pedidos disponibles para asignar")

    # 5. Crear RutaEntrega (simple: primera y última coordenada)
    coord_inicio = db.query(Cliente).filter_by(id=asignados[0].cliente_id).first().coordenadas
    coord_fin = db.query(Cliente).filter_by(id=asignados[-1].cliente_id).first().coordenadas
    ruta = RutaEntrega(
        coordenadas_inicio=coord_inicio,
        coordenadas_fin=coord_fin,
        distancia=distancia_pedido(asignados[-1]),  # simplificado
        tiempo_estimado="Desconocido"
    )
    db.add(ruta)
    db.commit()
    db.refresh(ruta)

    # 6. Crear AsignacionEntrega
    nueva_asignacion = AsignacionEntrega(
        id_distribuidor=distribuidor_id,
        ruta_id=ruta.ruta_id
    )
    db.add(nueva_asignacion)
    db.commit()
    db.refresh(nueva_asignacion)

    # 7. Crear PedidosAsignados
    for pedido in asignados:
        asignado = PedidoAsignado(
            pedido_id=pedido.id,
            asignacion_id=nueva_asignacion.id
        )
        db.add(asignado)

        pedido.estado = "asignado"

    db.commit()

    return nueva_asignacion