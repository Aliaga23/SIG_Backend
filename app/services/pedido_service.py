from sqlalchemy.orm import Session
from uuid import UUID
from app.models.pedido_model import Pedido, DetallePedido
from app.models.producto_model import Producto
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
        # Obtenemos el precio directamente del producto
        producto = db.query(Producto).filter(Producto.id == item.producto_id).first()
        if not producto:
            raise ValueError(f"Producto con ID {item.producto_id} no encontrado")
            
        precio_unitario = float(producto.precio)
        subtotal = precio_unitario * item.cantidad
        total += subtotal
        detalles.append(DetallePedido(
            producto_id=item.producto_id,
            cantidad=item.cantidad,
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

def obtener_detalles_pedido_con_precios(db: Session, pedido_id: UUID):
    """
    Obtiene los detalles completos de un pedido incluyendo los precios de los productos
    """
    pedido = obtener_pedido(db, pedido_id)
    if not pedido:
        return None
        
    # Procesamos los detalles para incluir precio unitario de cada producto
    detalles_completos = []
    for detalle in pedido.detalles:
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if producto:
            detalle_dict = {
                "id": detalle.id,
                "cantidad": detalle.cantidad,
                "precio_unitario": float(producto.precio),
                "producto_id": detalle.producto_id,
                "subtotal": float(producto.precio) * detalle.cantidad,
                "nombre_producto": producto.nombre
            }
            detalles_completos.append(detalle_dict)
            
    resultado = {
        "id": pedido.id,
        "fecha_pedido": pedido.fecha_pedido,
        "estado": pedido.estado,
        "total": float(pedido.total),
        "instrucciones_entrega": pedido.instrucciones_entrega,
        "cliente_id": pedido.cliente_id,
        "detalles": detalles_completos
    }
    
    return resultado
