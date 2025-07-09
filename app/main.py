from fastapi import FastAPI
from app.database import Base, engine

# Rutas
from app.routes import (
    distribuidor_routes,
    vehiculo_routes,
    cliente_routes,
    producto_routes,
    pedido_routes,
    pago_routes,
    ruta_entrega_routes,
    asignacion_routes,
    auth_routes,
    asignacion_vehiculo_routes,
    tienda_routes,
    entregas_routes
)

app = FastAPI(title="API Distribución de Zapatos")

# Crear tablas
Base.metadata.create_all(bind=engine)
# Asegurar que la columna asignacion_id exista en la tabla entrega (migración ligera)
from sqlalchemy import text
with engine.begin() as conn:
    conn.execute(text(
        "ALTER TABLE entrega ADD COLUMN IF NOT EXISTS asignacion_id UUID REFERENCES asignacion_entrega(id) ON DELETE CASCADE"
    ))

# Registrar routers
app.include_router(auth_routes.router)

app.include_router(distribuidor_routes.router)
app.include_router(vehiculo_routes.router)
app.include_router(cliente_routes.router)
app.include_router(producto_routes.router)
app.include_router(pedido_routes.router)
app.include_router(pago_routes.router)
app.include_router(ruta_entrega_routes.router)
app.include_router(asignacion_routes.router)
app.include_router(asignacion_vehiculo_routes.router)
app.include_router(tienda_routes.router)
app.include_router(entregas_routes.router)