from sqlalchemy.orm import Session
from uuid import UUID
from app.models.producto_model import Producto
from app.schemas.producto_schema import ProductoCreate, ProductoUpdate

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
