from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.cliente_model import Cliente
from app.models.distribuidor_model import Distribuidor
from app.auth.jwt_utils import verificar_token

security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_cliente(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verificar que el rol sea cliente
    if payload.get("role") != "cliente":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol de cliente")
    
    user = db.query(Cliente).filter(Cliente.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")
    return user

def get_current_distribuidor(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    # Verificar que el rol sea distribuidor
    if payload.get("role") != "distribuidor":
        raise HTTPException(status_code=403, detail="Acceso denegado: se requiere rol de distribuidor")
    
    user = db.query(Distribuidor).filter(Distribuidor.email == payload["sub"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="Distribuidor no encontrado")
    return user
