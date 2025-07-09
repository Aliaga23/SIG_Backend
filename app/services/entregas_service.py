from sqlalchemy.orm import Session
from uuid import UUID
from app.models.ruta_entrega_model import Entrega
from app.models.pedido_model import Pedido, DetallePedido
from app.services.producto_service import descontar_stock_por_pedido
from app.schemas.entrega_schema import EntregaUpdate

def completar_entrega(db: Session, entrega_id: UUID, datos: EntregaUpdate):
    ent: Entrega = db.query(Entrega).filter(Entrega.id_entrega==entrega_id).first()
    if not ent:
        return None

    primera_vez = ent.estado != "entregado"

    ent.coordenadas_fin = datos.coordenadas_fin
    ent.estado          = datos.estado
    ent.observaciones   = datos.observaciones

    if datos.estado == "entregado" and primera_vez:
        # Descontar stock usando el pedido asociado a esta entrega
        descontar_stock_por_pedido(db, ent.pedido_id)
        # Cambiar estado del pedido
        pedido: Pedido = db.query(Pedido).filter(Pedido.id==ent.pedido_id).first()
        if pedido:
            pedido.estado = "entregado"

    db.commit()
    db.refresh(ent)          
    return ent
