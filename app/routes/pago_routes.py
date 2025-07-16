from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
import os
try:
    import stripe
except ImportError:
    stripe = None

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

@router.post("/generar_pago_qr/")
def generar_pago_qr(monto_total: float, descripcion: str = "Pedido personalizado"):
    """
    Genera un Payment Link de Stripe para pagos con QR
    """
    try:
        if not stripe:
            raise HTTPException(status_code=500, detail="Stripe no está disponible")
            
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        # Crear el producto
        product = stripe.Product.create(name=descripcion)

        # Crear el precio (Stripe usa centavos)
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(monto_total * 100),
            currency="usd",
        )

        # Crear el Payment Link
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                "price": price.id,
                "quantity": 1,
            }],
        )

        return {
            "success": True,
            "payment_link": payment_link.url,
            "qr_url": payment_link.url,
            "monto": monto_total,
            "descripcion": descripcion
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando pago QR: {str(e)}")

@router.post("/generar_pago_qr_pedido/{pedido_id}")
def generar_pago_qr_pedido(pedido_id: UUID, db: Session = Depends(get_db)):
    """
    Genera un Payment Link de Stripe específico para un pedido y crea el registro de pago
    """
    from app.models.pedido_model import Pedido, DetallePedido
    from app.models.producto_model import Producto
    from app.models.pago_model import Pago
    
    try:
        # Verificar si ya existe un pago para este pedido
        pago_existente = db.query(Pago).filter(Pago.pedido_id == pedido_id).first()
        if pago_existente:
            raise HTTPException(status_code=400, detail="Ya existe un pago para este pedido")
        
        # Obtener el pedido
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if not pedido:
            raise HTTPException(status_code=404, detail="Pedido no encontrado")
        
        # Calcular el total del pedido
        detalles = db.query(DetallePedido).filter(DetallePedido.pedido_id == pedido_id).all()
        total = 0
        descripcion_items = []
        
        for detalle in detalles:
            producto = db.query(Producto).filter(Producto.id == detalle.producto_id).first()
            if producto:
                subtotal = float(producto.precio) * detalle.cantidad
                total += subtotal
                descripcion_items.append(f"{producto.nombre} x{detalle.cantidad}")
        
        if total == 0:
            raise HTTPException(status_code=400, detail="El pedido no tiene productos válidos")
        
        descripcion = f"Pedido #{str(pedido_id)[:8]} - {', '.join(descripcion_items[:3])}"
        if len(descripcion_items) > 3:
            descripcion += f" y {len(descripcion_items) - 3} más"
        
        if not stripe:
            raise HTTPException(status_code=500, detail="Stripe no está disponible")
            
        if not stripe:
            raise HTTPException(status_code=500, detail="Stripe no está disponible")
            
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        
        # Crear el producto
        product = stripe.Product.create(name=descripcion)

        # Crear el precio
        price = stripe.Price.create(
            product=product.id,
            unit_amount=int(total * 100),
            currency="usd",
        )

        # Crear el Payment Link
        payment_link = stripe.PaymentLink.create(
            line_items=[{
                "price": price.id,
                "quantity": 1,
            }],
            metadata={
                "pedido_id": str(pedido_id)
            }
        )

        # Crear el registro de pago en la base de datos
        nuevo_pago = Pago(
            metodo_pago="QR",
            monto=total,
            estado="pendiente",
            pedido_id=pedido_id,
            transaccion_id=payment_link.id
        )
        db.add(nuevo_pago)
        db.commit()
        db.refresh(nuevo_pago)

        return {
            "success": True,
            "pedido_id": str(pedido_id),
            "pago_id": str(nuevo_pago.id_pago),
            "payment_link": payment_link.url,
            "qr_url": payment_link.url,
            "total": total,
            "descripcion": descripcion,
            "productos": descripcion_items,
            "estado_pago": "pendiente"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando pago QR para pedido: {str(e)}")

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

@router.get("/estado_pago/{pedido_id}")
def verificar_estado_pago(pedido_id: UUID, db: Session = Depends(get_db)):
    """
    Verifica el estado actual del pago para un pedido específico
    """
    from app.models.pago_model import Pago
    
    pago = db.query(Pago).filter(Pago.pedido_id == pedido_id).first()
    
    if not pago:
        raise HTTPException(status_code=404, detail="No se encontró un pago para este pedido")
    
    return {
        "pedido_id": str(pedido_id),
        "pago_id": str(pago.id_pago),
        "estado": pago.estado,
        "monto": float(pago.monto),
        "metodo_pago": pago.metodo_pago,
        "fecha_pago": pago.fecha_pago,
        "transaccion_id": pago.transaccion_id
    }
