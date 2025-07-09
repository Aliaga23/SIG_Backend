
from __future__ import annotations

from uuid import UUID
from typing import List, Tuple

from sqlalchemy.orm import Session
from geopy.distance import geodesic

from app.models.ruta_entrega_model import RutaEntrega, Entrega
from app.models.tienda_model          import Tienda
from app.models.distribuidor_model    import Distribuidor
from app.models.cliente_model         import Cliente
from app.models.pedido_model          import Pedido           # para cambiar estado
from app.services.producto_service    import descontar_stock_por_pedido


# ─────────────────────────  CRUD BÁSICO  ────────────────────────── #
def crear_ruta_entrega(db: Session, datos):
    """Crea la cabecera RutaEntrega (no genera entregas)."""
    nueva = RutaEntrega(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def listar_rutas_entrega(db: Session):
    return db.query(RutaEntrega).all()


def obtener_ruta_entrega(db: Session, ruta_id: UUID):
    return (
        db.query(RutaEntrega)
          .filter(RutaEntrega.ruta_id == ruta_id)
          .first()
    )


def registrar_entrega(db: Session, datos):
    nueva = Entrega(**datos.dict())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


def listar_entregas(db: Session):
    return db.query(Entrega).all()


def obtener_entrega(db: Session, entrega_id: UUID):
    return (
        db.query(Entrega)
          .filter(Entrega.id_entrega == entrega_id)
          .first()
    )


def actualizar_estado_entrega(db: Session, entrega_id: UUID, nuevo_estado: str):
    ent = obtener_entrega(db, entrega_id)
    if ent:
        ent.estado = nuevo_estado
        db.commit()
        db.refresh(ent)
    return ent


def actualizar_observaciones_entrega(db: Session, entrega_id: UUID, observaciones: str):
    ent = obtener_entrega(db, entrega_id)
    if ent:
        ent.observaciones = observaciones
        db.commit()
        db.refresh(ent)
    return ent


def actualizar_ubicacion_entrega(db: Session, entrega_id: UUID, coordenadas: str):
    ent = obtener_entrega(db, entrega_id)
    if ent:
        ent.coordenadas_fin = coordenadas
        db.commit()
        db.refresh(ent)
    return ent


def calcular_ruta_optimizada(
    db: Session,
    tienda_id:     UUID,
    clientes_ids:  List[UUID],
    distribuidor_id: UUID,
) -> Tuple[RutaEntrega, List[Cliente]]:
    """
    Persiste una RutaEntrega y N Entrega-s en la BD.
    Orden de visita:
        Distribuidor ➜ Tienda ➜ Cliente1 ➜ Cliente2 ➜ … ➜ ClienteN
    Retorna la cabecera `RutaEntrega` + lista ordenada de `Cliente`.
    """
    tienda  : Tienda       = db.query(Tienda).filter(Tienda.id == tienda_id).first()
    dist    : Distribuidor = db.query(Distribuidor).filter(Distribuidor.id == distribuidor_id).first()
    if not tienda:      raise ValueError("Tienda no encontrada")
    if not dist:        raise ValueError("Distribuidor no encontrado")
    if not all([dist.latitud, dist.longitud, tienda.latitud, tienda.longitud]):
        raise ValueError("El distribuidor o la tienda no tienen coordenadas registradas")

    clientes: List[Tuple[Cliente, Tuple[float,float]]] = []
    for cid in clientes_ids:
        cli = db.query(Cliente).filter(Cliente.id == cid).first()
        if not cli or not cli.coordenadas:   # vacío o NULL
            continue
        try:
            lat, lon = map(float, cli.coordenadas.split(","))
            clientes.append((cli, (lat, lon)))
        except (ValueError, TypeError):
            continue
    if not clientes:
        raise ValueError("No hay clientes válidos con coordenadas")

    ruta_clientes: List[Cliente]  = []
    disponibles = clientes.copy()
    punto_actual = (tienda.latitud, tienda.longitud)
    while disponibles:
        cli_cercano = min(disponibles, key=lambda c: geodesic(punto_actual, c[1]).km)
        ruta_clientes.append(cli_cercano[0])
        punto_actual     = cli_cercano[1]
        disponibles.remove(cli_cercano)

    distancia_km = geodesic(
        (dist.latitud, dist.longitud),
        (tienda.latitud, tienda.longitud)
    ).km
    if ruta_clientes:
        # Tienda-> Primer cliente y ya avanza
        lat, lon = map(float, ruta_clientes[0].coordenadas.split(","))
        distancia_km += geodesic((tienda.latitud, tienda.longitud), (lat, lon)).km
        # Entre clientes consecutivos
        for a, b in zip(ruta_clientes[:-1], ruta_clientes[1:]):
            la1, lo1 = map(float, a.coordenadas.split(","))
            la2, lo2 = map(float, b.coordenadas.split(","))
            distancia_km += geodesic((la1, lo1), (la2, lo2)).km

    # 5) ─── Persistir RutaEntrega + Entregas ───────────────────────
    ruta = RutaEntrega(
        coordenadas_inicio = f"{tienda.latitud},{tienda.longitud}",
        coordenadas_fin    = ruta_clientes[-1].coordenadas if ruta_clientes else f"{tienda.latitud},{tienda.longitud}",
        distancia          = distancia_km,
        tiempo_estimado    = f"{int(distancia_km * 2)} mins"   # 2 min/km: heurística simple
    )
    db.add(ruta)
    db.flush()                     

    entregas = [
        Entrega(
            ruta_id        = ruta.ruta_id,
            cliente_id     = cli.id,
            orden_entrega  = pos,
            estado         = "pendiente"        # pendiente por defecto
        )
        for pos, cli in enumerate(ruta_clientes, start=1)
    ]
    db.add_all(entregas)
    db.commit()
    db.refresh(ruta)

    return ruta, ruta_clientes


# ────────────────────  COMPLETAR ENTREGA  ─────────────────────── #
def completar_entrega(
    db: Session,
    entrega_id: UUID,
    coordenadas_fin: str,
    estado: str = "entregado",
    observaciones: str | None = None,
):
    """
    Actualiza la entrega y, si es la PRIMERA vez que pasa a 'entregado',
    descuenta inventario y cambia el estado del pedido.
    """
    ent: Entrega | None = obtener_entrega(db, entrega_id)
    if not ent:
        return None

    primera_vez = ent.estado != "entregado"
    ent.coordenadas_fin = coordenadas_fin
    ent.estado          = estado
    ent.observaciones   = observaciones

    if estado == "entregado" and primera_vez:
        # 1) Descontar stock (sólo si la Entrega referencia un pedido)
        if ent.pedido_id:
            descontar_stock_por_pedido(db, ent.pedido_id)

            # 2) Cambiar estado del pedido
            ped: Pedido | None = db.query(Pedido).filter(Pedido.id == ent.pedido_id).first()
            if ped:
                ped.estado = "entregado"

    db.commit()
    db.refresh(ent)
    return ent
