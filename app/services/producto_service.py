from sqlalchemy.orm import Session
from uuid import UUID
from app.models.producto_model import Producto
from app.schemas.producto_schema import ProductoCreate, ProductoUpdate
from app.models.pedido_model import DetallePedido   # ⬅️ al inicio

def crear_producto(db: Session, datos: ProductoCreate):
    nuevo = Producto(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def listar_productos(db: Session):
    return db.query(Producto).all()

def obtener_producto(db: Session, producto_id: UUID):
    return db.query(Producto).filter(Producto.id == producto_id).first()

def actualizar_producto(db: Session, producto_id: UUID, datos: ProductoUpdate):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        for key, value in datos.dict().items():
            setattr(producto, key, value)
        db.commit()
        db.refresh(producto)
    return producto

def actualizar_stock(db: Session, producto_id: UUID, nuevo_stock: int):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        producto.stock = nuevo_stock
        db.commit()
        db.refresh(producto)
    return producto

def eliminar_producto(db: Session, producto_id: UUID):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if producto:
        db.delete(producto)
        db.commit()
    return producto

def descontar_stock_por_pedido(db: Session, pedido_id: UUID):
    """
    Reduce el stock de los productos cuando se confirma un pedido
    """
    from app.models.pedido_model import DetallePedido, Pedido
    
    # Verificar si el pedido existe y está en estado aceptado
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido or pedido.estado not in ["asignado", "en_entrega", "entregado"]:
        return False
    
    # Obtener los detalles del pedido
    detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
    
    for detalle in detalles:
        # Obtener el producto
        producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
        if producto:
            # Actualizar el stock
            if producto.stock >= detalle.cantidad:
                producto.stock -= detalle.cantidad
                db.commit()
            else:
                # Si no hay suficiente stock, actualizar lo que se pueda
                producto.stock = 0
                db.commit()
    
    return True
