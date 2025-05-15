from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import bcrypt
from uuid import UUID

from app.database import SessionLocal
from app.models.cliente_model import Cliente
from app.models.distribuidor_model import Distribuidor
from app.auth.jwt_utils import crear_token
from app.schemas.auth_schema import LoginRequest

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
