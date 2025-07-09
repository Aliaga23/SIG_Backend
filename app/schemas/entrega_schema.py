from typing import Literal
from pydantic import BaseModel, Field

class EntregaUpdate(BaseModel):
    coordenadas_fin: str          
    estado: Literal["entregado", "fallido"] = "entregado"
    observaciones: str | None = None
