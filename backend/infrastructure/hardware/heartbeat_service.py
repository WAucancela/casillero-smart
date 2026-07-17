import asyncio
import logging
from typing import Optional
import sqlalchemy as sa
from infrastructure.database.conexion import AsyncSessionLocal
from infrastructure.hardware.controlador_mqtt import controlador_mqtt

logger = logging.getLogger(__name__)

TOPIC_PING = "casilleros/respuesta/+/ping"
TOPIC_OFFLINE = "casilleros/respuesta/+/offline"

# Loop principal de FastAPI; los callbacks MQTT llegan en el hilo de paho
_loop: Optional[asyncio.AbstractEventLoop] = None


def registrar_heartbeat(loop: asyncio.AbstractEventLoop):
    """Suscribe los topics de ping/offline de los controladores ESP32."""
    global _loop
    _loop = loop
    controlador_mqtt.suscribir(TOPIC_PING, _on_ping)
    controlador_mqtt.suscribir(TOPIC_OFFLINE, _on_offline)
    logger.info("Heartbeat de controladores registrado")


def _on_ping(topic: str, payload: dict):
    # topic: casilleros/respuesta/{controlador_id}/ping
    controlador_id = payload.get("controlador_id") or topic.split("/")[2]
    _programar(_actualizar_ping(controlador_id, payload.get("ip")))


def _on_offline(topic: str, payload: dict):
    controlador_id = topic.split("/")[2]
    logger.warning(f"Controlador {controlador_id} desconectado (last will MQTT)")


def _programar(coro):
    if _loop is None or _loop.is_closed():
        return
    asyncio.run_coroutine_threadsafe(coro, _loop)


async def _actualizar_ping(controlador_id: str, ip: Optional[str]):
    try:
        async with AsyncSessionLocal() as session:
            resultado = await session.execute(
                sa.text(
                    "UPDATE controladores "
                    "SET ultimo_ping = NOW(), "
                    "    ip_local = COALESCE(CAST(:ip AS INET), ip_local) "
                    "WHERE id = :id"
                ),
                {"id": controlador_id, "ip": ip},
            )
            await session.commit()
            if resultado.rowcount == 0:
                logger.warning(
                    f"Ping de controlador no registrado en BD: {controlador_id}"
                )
    except Exception as e:
        logger.error(f"Error actualizando ping de {controlador_id}: {e}")
