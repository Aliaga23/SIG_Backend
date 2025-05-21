
# API de Distribución de Zapatos

Este backend ha sido desarrollado con FastAPI para gestionar un sistema de distribución de zapatos. Implementa una arquitectura modular con rutas separadas por entidad y conexión a base de datos mediante SQLAlchemy.

## Tecnologías utilizadas

- Python 3.x
- FastAPI
- SQLAlchemy
- PostgreSQL (puede adaptarse a otras bases de datos compatibles con SQLAlchemy)
- Uvicorn (para ejecución del servidor)
- JWT (para autenticación)

## Estructura del proyecto

```
SIG_Backend-main/
├── app/
│   ├── auth/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── schemas/
│   ├── database.py
│   ├── main.py
├── requirements.txt
├── Procfile
└── README.md
```

## Endpoints principales

Los endpoints están organizados por entidades. A continuación, se enumeran las rutas principales:

### Autenticación

- `POST /auth/login`: Inicia sesión con usuario y contraseña.
- `GET /auth/profile`: Obtiene el perfil del usuario autenticado.

### Distribuidores

- `GET /distribuidores/`: Lista todos los distribuidores.
- `POST /distribuidores/`: Crea un nuevo distribuidor.
- `GET /distribuidores/{id}`: Obtiene un distribuidor por ID.
- `PUT /distribuidores/{id}`: Actualiza un distribuidor.
- `DELETE /distribuidores/{id}`: Elimina un distribuidor.

### Vehículos

- `GET /vehiculos/`
- `POST /vehiculos/`
- `GET /vehiculos/{id}`
- `PUT /vehiculos/{id}`
- `DELETE /vehiculos/{id}`

### Clientes

- `GET /clientes/`
- `POST /clientes/`
- `GET /clientes/{id}`
- `PUT /clientes/{id}`
- `DELETE /clientes/{id}`

### Productos

- `GET /productos/`
- `POST /productos/`
- `GET /productos/{id}`
- `PUT /productos/{id}`
- `DELETE /productos/{id}`

### Pedidos

- `GET /pedidos/`
- `POST /pedidos/`
- `GET /pedidos/{id}`
- `PUT /pedidos/{id}`
- `DELETE /pedidos/{id}`

### Pagos

- `GET /pagos/`
- `POST /pagos/`
- `GET /pagos/{id}`
- `PUT /pagos/{id}`
- `DELETE /pagos/{id}`

### Rutas de entrega

- `GET /rutas/`
- `POST /rutas/`
- `GET /rutas/{id}`
- `PUT /rutas/{id}`
- `DELETE /rutas/{id}`

### Asignaciones

- `GET /asignaciones/`
- `POST /asignaciones/`
- `GET /asignaciones/{id}`
- `PUT /asignaciones/{id}`
- `DELETE /asignaciones/{id}`

## Instalación y ejecución

1. Clona el repositorio:

```bash
git clone https://github.com/tu-usuario/SIG_Backend-main.git
cd SIG_Backend-main
```

2. Instala los requerimientos:

```bash
pip install -r requirements.txt
```

3. Configura la base de datos en `app/database.py`.

4. Ejecuta el servidor:

```bash
uvicorn app.main:app --reload
```

## Notas adicionales

- Las rutas están protegidas con autenticación JWT.
- Se recomienda configurar variables de entorno para los secretos y la cadena de conexión a base de datos.
- El archivo `Procfile` está preparado para despliegue en plataformas como Heroku.

