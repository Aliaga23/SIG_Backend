from sqlalchemy.orm import Session
from uuid import UUID
from app.models.pedido_model import Pedido, DetallePedido
from app.schemas.pedido_schema import PedidoCreate, PedidoEstadoUpdate

def crear_pedido(db: Session, datos: PedidoCreate):
    pedido = Pedido(
        cliente_id=datos.cliente_id,
        instrucciones_entrega=datos.instrucciones_entrega,
        estado="pendiente"
    )
    total = 0
    detalles = []
    for item in datos.detalles:
        subtotal = item.precio_unitario * item.cantidad
        total += subtotal
        detalles.append(DetallePedido(
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            precio_unitario=item.precio_unitario,
            pedido=pedido
        ))

    pedido.total = total
    db.add(pedido)
    db.add_all(detalles)
    db.commit()
    db.refresh(pedido)
    return pedido

def listar_pedidos(db: Session):
    return db.query(Pedido).all()

def obtener_pedido(db: Session, pedido_id: UUID):
    return db.query(Pedido).filter(Pedido.id == pedido_id).first()

def actualizar_estado_pedido(db: Session, pedido_id: UUID, estado: str):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        pedido.estado = estado
        db.commit()
        db.refresh(pedido)
    return pedido

def eliminar_pedido(db: Session, pedido_id: UUID):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if pedido:
        db.delete(pedido)
        db.commit()
    return pedido
