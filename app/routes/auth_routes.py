from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import bcrypt
from uuid import UUID

from app.database import SessionLocal
from app.models.cliente_model import Cliente
from app.models.distribuidor_model import Distribuidor
from app.auth.jwt_utils import crear_token
from app.schemas.auth_schema import LoginRequest
from app.auth.dependencies import get_current_distribuidor, get_current_cliente

security = HTTPBearer()

router = APIRouter(prefix="/auth", tags=["Autenticación"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = request.email
    password = request.password

    user = db.query(Cliente).filter(Cliente.email == email).first()
    role = "cliente"

    if not user:
        user = db.query(Distribuidor).filter(Distribuidor.email == email).first()
        role = "distribuidor"

    if not user or not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    token = crear_token({"sub": user.email, "role": role})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/verify-distribuidor", dependencies=[Depends(security)])
def verificar_distribuidor(distribuidor: Distribuidor = Depends(get_current_distribuidor)):
    """
    Endpoint para verificar que la autenticación del distribuidor funciona correctamente
    """
    return {
        "mensaje": "Autenticación exitosa",
        "distribuidor_id": distribuidor.id,
        "email": distribuidor.email,
        "nombre": distribuidor.nombre
    }

@router.get("/verify-cliente", dependencies=[Depends(security)]) 
def verificar_cliente(cliente: Cliente = Depends(get_current_cliente)):
    """
    Endpoint para verificar que la autenticación del cliente funciona correctamente
    """
    return {
        "mensaje": "Autenticación exitosa",
        "cliente_id": cliente.id,
        "email": cliente.email,
        "nombre": cliente.nombre
    }

@router.get("/debug-token", dependencies=[Depends(security)])
def debug_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    Endpoint de debug para ver qué contiene el token (usando el mismo esquema que otros endpoints)
    """
    from app.auth.jwt_utils import verificar_token
    
    token = credentials.credentials
    payload = verificar_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # También verificar si el usuario existe en la base de datos
    email = payload.get("sub")
    role = payload.get("role")
    
    user_info = None
    if role == "distribuidor":
        user = db.query(Distribuidor).filter(Distribuidor.email == email).first()
        if user:
            user_info = {"id": str(user.id), "nombre": user.nombre, "email": user.email}
    elif role == "cliente":
        user = db.query(Cliente).filter(Cliente.email == email).first()
        if user:
            user_info = {"id": str(user.id), "nombre": user.nombre, "email": user.email}
    
    return {
        "token_valido": True,
        "payload": payload,
        "email": email,
        "role": role,
        "exp": payload.get("exp"),
        "usuario_encontrado": user_info is not None,
        "usuario_info": user_info
    }

@router.post("/debug-token-manual")
def debug_token_manual(token: str):
    """
    Endpoint de debug para ver qué contiene un token específico (sin autenticación automática)
    """
    from app.auth.jwt_utils import verificar_token
    
    payload = verificar_token(token)
    
    if not payload:
        return {"error": "Token inválido"}
    
    return {
        "token_valido": True,
        "payload": payload,
        "email": payload.get("sub"),
        "role": payload.get("role"),
        "exp": payload.get("exp")
    }
