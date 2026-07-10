from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from api.middlewares.auth_middleware import solo_super
from infrastructure.database.conexion import get_db
from infrastructure.database.terminal_repo import TerminalRepository
from infrastructure.hardware.controlador_mqtt import controlador_mqtt

router = APIRouter()

# Terminal considerada "activa" si hizo contacto en los últimos 2 minutos
_TIMEOUT_ACTIVO_SEG = 120


# ── GET /api/hardware/terminales ──────────────────────────────────────────────
@router.get("/terminales", summary="Listar terminales ZKTeco conectadas")
async def listar_terminales(
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    terminales = await TerminalRepository(db).listar()
    ahora = datetime.now()
    return [
        {
            "id":            t.id,
            "numero_serie":  t.sn,
            "descripcion":   t.descripcion or f"Terminal ZKTeco SenseFace 2A ({t.sn})",
            "ip_local":      t.ip or "—",
            "piso":          t.piso or 1,
            "activo":        t.ultimo_contacto is not None
                             and (ahora - t.ultimo_contacto).total_seconds() < _TIMEOUT_ACTIVO_SEG,
            "autorizado":      t.autorizado,
            "ultimo_contacto": t.ultimo_contacto.isoformat() if t.ultimo_contacto else None,
            "ultimo_evento":   t.ultimo_evento.isoformat()   if t.ultimo_evento   else None,
        }
        for t in terminales
    ]


class AutorizarTerminalRequest(BaseModel):
    autorizado: bool


# ── PATCH /api/hardware/terminales/{id}/autorizar ─────────────────────────────
@router.patch("/terminales/{terminal_id}/autorizar", summary="Autorizar o revocar un terminal ZKTeco")
async def autorizar_terminal(
    terminal_id: int,
    body: AutorizarTerminalRequest,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    terminal = await TerminalRepository(db).autorizar(terminal_id, body.autorizado)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal no encontrada")
    return {"id": terminal.id, "numero_serie": terminal.sn, "autorizado": terminal.autorizado}


# ── GET /api/hardware/controladores ──────────────────────────────────────────
@router.get("/controladores", summary="Listar controladores de cerraduras")
async def listar_controladores(admin: dict = Depends(solo_super)):
    mqtt_ok = controlador_mqtt._conectado
    return [
        {
            "id":             1,
            "nombre":         "Broker MQTT (Mosquitto)",
            "descripcion":    "Controlador central de cerraduras vía MQTT",
            "ip_local":       "mosquitto",
            "piso":           0,
            "num_puertas":    0,
            "mqtt_conectado": mqtt_ok,
            "activo":         mqtt_ok,
        }
    ]


# ── POST /api/hardware/{id}/ping ──────────────────────────────────────────────
@router.post("/{hardware_id}/ping", summary="Hacer ping a una terminal")
async def ping_hardware(
    hardware_id: int,
    db: AsyncSession = Depends(get_db),
    admin: dict = Depends(solo_super),
):
    terminal = await TerminalRepository(db).obtener_por_id(hardware_id)
    if not terminal:
        raise HTTPException(status_code=404, detail="Terminal no encontrada")

    inicio = datetime.now()
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.get(f"http://{terminal.ip}/iclock/cdata?SN={terminal.sn}&options=")
        latencia = int((datetime.now() - inicio).total_seconds() * 1000)
        return {"ok": True, "latencia_ms": latencia}
    except Exception:
        latencia = int((datetime.now() - inicio).total_seconds() * 1000)
        return {"ok": False, "latencia_ms": latencia}
