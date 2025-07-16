from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import SessionLocal
from app.schemas.cliente_schema import ClienteCreate, ClienteUpdate, ClienteOut
from app.services import cliente_service
from app.auth.dependencies import get_current_cliente
from app.models.cliente_model import Cliente

router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("", response_model=ClienteOut)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    return cliente_service.crear_cliente(db, cliente)

@router.get("", response_model=list[ClienteOut])
def listar_clientes(db: Session = Depends(get_db)):
    return cliente_service.listar_clientes(db)

@router.get("/perfil", response_model=ClienteOut)
def obtener_perfil_cliente(cliente_actual: Cliente = Depends(get_current_cliente)):
    """
    Endpoint protegido que requiere autenticación Bearer.
    Retorna el perfil del cliente autenticado.
    """
    return cliente_actual

@router.get("/mis-pedidos")
def obtener_mis_pedidos(
    cliente_actual: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial completo de pedidos del cliente autenticado
    """
    from app.models.pedido_model import Pedido, DetallePedido
    from app.models.producto_model import Producto
    from app.models.pago_model import Pago
    
    pedidos = db.query(Pedido).filter(
        Pedido.cliente_id == cliente_actual.id
    ).order_by(Pedido.fecha_pedido.desc()).all()
    
    if not pedidos:
        return {
            "pedidos": [],
            "total_pedidos": 0,
            "mensaje": "No tienes pedidos registrados"
        }
    
    resultado = []
    for pedido in pedidos:
        # Obtener detalles del pedido
        detalles = db.query(DetallePedido).filter(
            DetallePedido.pedido_id == pedido.id
        ).all()
        
        productos = []
        total_pedido = 0
        
        for detalle in detalles:
            producto = db.query(Producto).filter(
                Producto.id == detalle.producto_id
            ).first()
            if producto:
                subtotal = float(producto.precio) * detalle.cantidad
                total_pedido += subtotal
                productos.append({
                    "producto_id": str(producto.id),
                    "nombre": producto.nombre,
                    "precio": float(producto.precio),
                    "cantidad": detalle.cantidad,
                    "subtotal": subtotal
                })
        
        # Obtener información del pago
        pago = db.query(Pago).filter(Pago.pedido_id == pedido.id).first()
        info_pago = None
        if pago:
            info_pago = {
                "pago_id": str(pago.id_pago),
                "estado": pago.estado,
                "metodo_pago": pago.metodo_pago,
                "fecha_pago": pago.fecha_pago
            }
        
        pedido_data = {
            "pedido_id": str(pedido.id),
            "fecha_pedido": pedido.fecha_pedido,
            "estado": pedido.estado,
            "total": total_pedido,
            "productos": productos,
            "pago": info_pago
        }
        resultado.append(pedido_data)
    
    return {
        "pedidos": resultado,
        "total_pedidos": len(resultado)
    }

@router.get("/mis-entregas")
def obtener_mis_entregas(
    cliente_actual: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    """
    Obtiene las entregas del cliente con información del distribuidor y seguimiento
    """
    from app.models.ruta_entrega_model import Entrega
    from app.models.asignacion_model import AsignacionEntrega
    from app.models.distribuidor_model import Distribuidor
    from app.models.pedido_model import Pedido, DetallePedido
    from app.models.producto_model import Producto
    
    entregas = db.query(Entrega).join(AsignacionEntrega).filter(
        Entrega.cliente_id == cliente_actual.id
    ).order_by(Entrega.fecha_hora_reg.desc()).all()
    
    if not entregas:
        return {
            "entregas": [],
            "total_entregas": 0,
            "mensaje": "No tienes entregas registradas"
        }
    
    resultado = []
    for entrega in entregas:
        # Obtener asignación y distribuidor
        asignacion = db.query(AsignacionEntrega).filter(
            AsignacionEntrega.id == entrega.asignacion_id
        ).first()
        
        distribuidor = None
        ubicacion_distribuidor = None
        
        if asignacion:
            distribuidor = db.query(Distribuidor).filter(
                Distribuidor.id == asignacion.id_distribuidor
            ).first()
            
            # Si la entrega está pendiente, mostrar ubicación del distribuidor
            if entrega.estado == "pendiente" and distribuidor:
                # Usar siempre la ubicación actual del perfil del distribuidor
                ubicacion_distribuidor = f"{distribuidor.latitud},{distribuidor.longitud}"
        
        # Obtener información del pedido y productos
        pedido_info = None
        if entrega.pedido_id:
            pedido = db.query(Pedido).filter(Pedido.id == entrega.pedido_id).first()
            if pedido:
                detalles = db.query(DetallePedido).filter(
                    DetallePedido.pedido_id == pedido.id
                ).all()
                
                productos = []
                for detalle in detalles:
                    producto = db.query(Producto).filter(
                        Producto.id == detalle.producto_id
                    ).first()
                    if producto:
                        productos.append({
                            "nombre": producto.nombre,
                            "cantidad": detalle.cantidad
                        })
                
                pedido_info = {
                    "pedido_id": str(pedido.id),
                    "estado_pedido": pedido.estado,
                    "productos": productos
                }
        
        entrega_data = {
            "entrega_id": str(entrega.id_entrega),
            "fecha_registro": entrega.fecha_hora_reg,
            "estado": entrega.estado,
            "orden_entrega": entrega.orden_entrega,
            "coordenadas_destino": entrega.coordenadas_fin,
            "observaciones": entrega.observaciones,
            "pedido": pedido_info,
            "distribuidor": {
                "nombre": f"{distribuidor.nombre} {distribuidor.apellido}" if distribuidor else "No asignado",
                "telefono": distribuidor.telefono if distribuidor else None,
                "ubicacion_actual": ubicacion_distribuidor if entrega.estado == "pendiente" else None
            } if distribuidor else None
        }
        resultado.append(entrega_data)
    
    return {
        "entregas": resultado,
        "total_entregas": len(resultado),
        "entregas_pendientes": len([e for e in resultado if e["estado"] == "pendiente"]),
        "entregas_completadas": len([e for e in resultado if e["estado"] == "entregado"])
    }

@router.get("/seguimiento-entrega/{entrega_id}")
def seguimiento_entrega(
    entrega_id: UUID,
    cliente_actual: Cliente = Depends(get_current_cliente),
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de seguimiento para una entrega específica
    """
    from app.models.ruta_entrega_model import Entrega, RutaEntrega
    from app.models.asignacion_model import AsignacionEntrega
    from app.models.distribuidor_model import Distribuidor
    
    entrega = db.query(Entrega).filter(
        Entrega.id_entrega == entrega_id,
        Entrega.cliente_id == cliente_actual.id
    ).first()
    
    if not entrega:
        raise HTTPException(
            status_code=404, 
            detail="Entrega no encontrada o no pertenece a este cliente"
        )
    
    # Obtener información del distribuidor y asignación
    asignacion = db.query(AsignacionEntrega).filter(
        AsignacionEntrega.id == entrega.asignacion_id
    ).first()
    
    distribuidor = None
    ruta = None
    ubicacion_distribuidor = None
    
    if asignacion:
        distribuidor = db.query(Distribuidor).filter(
            Distribuidor.id == asignacion.id_distribuidor
        ).first()
        
        ruta = db.query(RutaEntrega).filter(
            RutaEntrega.ruta_id == asignacion.ruta_id
        ).first()
        
        # Obtener ubicación actual del distribuidor si la entrega está pendiente
        if entrega.estado == "pendiente" and distribuidor:
            # Usar siempre la ubicación actual del perfil del distribuidor
            ubicacion_distribuidor = f"{distribuidor.latitud},{distribuidor.longitud}"
    
    return {
        "entrega": {
            "entrega_id": str(entrega.id_entrega),
            "estado": entrega.estado,
            "orden_entrega": entrega.orden_entrega,
            "coordenadas_destino": entrega.coordenadas_fin,
            "fecha_registro": entrega.fecha_hora_reg,
            "observaciones": entrega.observaciones
        },
        "distribuidor": {
            "nombre": f"{distribuidor.nombre} {distribuidor.apellido}" if distribuidor else "No asignado",
            "telefono": distribuidor.telefono if distribuidor else None,
            "estado": distribuidor.estado if distribuidor else None,
            "ubicacion_actual": ubicacion_distribuidor if entrega.estado == "pendiente" else None
        } if distribuidor else None,
        "ruta": {
            "coordenadas_inicio": ruta.coordenadas_inicio if ruta else None,
            "coordenadas_fin": ruta.coordenadas_fin if ruta else None,
            "distancia": float(ruta.distancia) if ruta and ruta.distancia else None,
            "tiempo_estimado": ruta.tiempo_estimado if ruta else None
        } if ruta else None,
        "seguimiento": {
            "puede_rastrear": entrega.estado == "pendiente",
            "mensaje": _obtener_mensaje_seguimiento(entrega.estado)
        }
    }

def _obtener_mensaje_seguimiento(estado: str) -> str:
    """Obtiene un mensaje descriptivo del estado de la entrega"""
    mensajes = {
        "pendiente": "Tu pedido está en camino. El distribuidor se dirigirá a tu ubicación pronto.",
        "entregado": "¡Tu pedido ha sido entregado exitosamente!",
        "fallido": "Hubo un problema con la entrega. Contacta con soporte."
    }
    return mensajes.get(estado, f"Estado desconocido: {estado}")

@router.get("/{id}", response_model=ClienteOut)
def obtener_cliente(id: UUID, db: Session = Depends(get_db)):
    cliente = cliente_service.obtener_cliente(db, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.put("/{id}", response_model=ClienteOut)
def actualizar_cliente(id: UUID, datos: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = cliente_service.actualizar_cliente(db, id, datos)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente

@router.delete("/{id}")
def eliminar_cliente(id: UUID, db: Session = Depends(get_db)):
    cliente = cliente_service.eliminar_cliente(db, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"mensaje": "Cliente eliminado correctamente"}
