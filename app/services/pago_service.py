import os
import stripe
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.pago_model import Pago
from app.schemas.pago_schema import PagoCreate

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def crear_pago(db: Session, datos: PagoCreate):
    nuevo = Pago(**datos.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

def listar_pagos(db: Session):
    return db.query(Pago).all()

def obtener_pago(db: Session, pago_id: UUID):
    return db.query(Pago).filter(Pago.id_pago == pago_id).first()

def actualizar_estado_pago(db: Session, pago_id: UUID, estado: str):
    pago = db.query(Pago).filter(Pago.id_pago == pago_id).first()
    if pago:
        pago.estado = estado
        db.commit()
        db.refresh(pago)
    return pago

def crear_sesion_stripe(monto: float, pedido_id: str):
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "unit_amount": int(monto * 100),
                "product_data": {
                    "name": f"Pago de Pedido #{pedido_id}"
                }
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=os.getenv("FRONTEND_URL") + "/exito",
        cancel_url=os.getenv("FRONTEND_URL") + "/cancelado",
        metadata={"pedido_id": pedido_id}
    )
    return session.url

def procesar_webhook(event, db: Session):
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        pedido_id = session["metadata"]["pedido_id"]
        pago = db.query(Pago).filter(Pago.pedido_id == UUID(pedido_id)).first()
        if pago:
            pago.estado = "pagado"
            pago.transaccion_id = session["payment_intent"]
            db.commit()
            db.refresh(pago)
