from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.producto_schema import ProductoCreate, ProductoUpdate, ProductoOut
from app.services import producto_service

router = APIRouter(
    prefix="/productos",
    tags=["Productos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=ProductoOut)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    return producto_service.crear_producto(db, producto)

@router.get("", response_model=list[ProductoOut])
def listar_productos(db: Session = Depends(get_db)):
    return producto_service.listar_productos(db)

@router.get("/{id}", response_model=ProductoOut)
def obtener_producto(id: UUID, db: Session = Depends(get_db)):
    producto = producto_service.obtener_producto(db, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.put("/{id}", response_model=ProductoOut)
def actualizar_producto(id: UUID, datos: ProductoUpdate, db: Session = Depends(get_db)):
    producto = producto_service.actualizar_producto(db, id, datos)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.patch("/{id}/stock", response_model=ProductoOut)
def actualizar_stock(id: UUID, nuevo_stock: int, db: Session = Depends(get_db)):
    producto = producto_service.actualizar_stock(db, id, nuevo_stock)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto

@router.delete("/{id}")
def eliminar_producto(id: UUID, db: Session = Depends(get_db)):
    producto = producto_service.eliminar_producto(db, id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return {"mensaje": "Producto eliminado correctamente"}
