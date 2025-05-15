from sqlalchemy.orm import Session
from uuid import UUID
import bcrypt
from app.models.cliente_model import Cliente
from app.schemas.cliente_schema import ClienteCreate, ClienteUpdate

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def crear_cliente(db: Session, datos: ClienteCreate):
    hashed_pw = hash_password(datos.password)
    nuevo = Cliente(**datos.dict(exclude={"password"}), password=hashed_pw)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def listar_clientes(db: Session):
    return db.query(Cliente).all()

def obtener_cliente(db: Session, cliente_id: UUID):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()

def actualizar_cliente(db: Session, cliente_id: UUID, datos: ClienteUpdate):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente:
        for key, value in datos.dict().items():
            if key == "password":
                value = hash_password(value)
            setattr(cliente, key, value)
        db.commit()
        db.refresh(cliente)
    return cliente

def eliminar_cliente(db: Session, cliente_id: UUID):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if cliente:
        db.delete(cliente)
        db.commit()
    return cliente
