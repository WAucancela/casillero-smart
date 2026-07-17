from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import usuarios_routes, casilleros_routes, accesos_routes, reportes_routes, auth_routes, hardware_routes, admin_routes
from api.middlewares.error_middleware import error_handler
from config.settings import settings
from config.logging import setup_logging
from infrastructure.database.conexion import init_db
from infrastructure.zkteco.adms_router import router as zkteco_router
from infrastructure.hardware.controlador_mqtt import controlador_mqtt
from infrastructure.hardware.heartbeat_service import registrar_heartbeat
from infrastructure.database.terminal_repo import TerminalZKTecoModel  # registrar en metadata

setup_logging()

app = FastAPI(
    title="Sistema de Casilleros Automatizados",
    version="1.0.0",
    description="Backend para gestion de casilleros con reconocimiento facial"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(error_handler)

app.include_router(auth_routes.router, prefix="/api/auth", tags=["Auth"])
app.include_router(usuarios_routes.router, prefix="/api/usuarios", tags=["Usuarios"])
app.include_router(casilleros_routes.router, prefix="/api/casilleros", tags=["Casilleros"])
app.include_router(accesos_routes.router, prefix="/api/accesos", tags=["Accesos"])
app.include_router(reportes_routes.router, prefix="/api/reportes", tags=["Reportes"])
app.include_router(hardware_routes.router, prefix="/api/hardware", tags=["Hardware"])
app.include_router(admin_routes.router, prefix="/api/admin", tags=["Administradores"])
app.include_router(zkteco_router)  # /iclock/ — protocolo ADMS Push del SenseFace 2A

@app.on_event("startup")
async def startup():
    await init_db()
    try:
        controlador_mqtt.conectar()
        import asyncio
        registrar_heartbeat(asyncio.get_running_loop())
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"No se pudo conectar al broker MQTT: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
