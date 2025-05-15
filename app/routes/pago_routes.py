from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
import os, stripe

from app.database import SessionLocal
from app.schemas.pago_schema import PagoCreate, PagoOut, PagoEstadoUpdate
from app.services import pago_service

router = APIRouter(
    prefix="/pagos",
    tags=["Pagos"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=PagoOut)
def registrar_pago(pago: PagoCreate, db: Session = Depends(get_db)):
    return pago_service.crear_pago(db, pago)

@router.get("", response_model=list[PagoOut])
def listar(db: Session = Depends(get_db)):
    return pago_service.listar_pagos(db)

@router.get("/{id}", response_model=PagoOut)
def obtener(id: UUID, db: Session = Depends(get_db)):
    pago = pago_service.obtener_pago(db, id)
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    return pago

@router.patch("/{id}/estado", response_model=PagoOut)
def cambiar_estado(id: UUID, body: PagoEstadoUpdate, db: Session = Depends(get_db)):
    return pago_service.actualizar_estado_pago(db, id, body.estado)

@router.get("/stripe/create-session/{pedido_id}")
def stripe_checkout(pedido_id: UUID, monto: float):
    url = pago_service.crear_sesion_stripe(monto, str(pedido_id))
    return {"checkout_url": url}

@router.post("/stripe/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Payload inválido")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma inválida")

    background_tasks.add_task(pago_service.procesar_webhook, event, db)
    return {"ok": True}
