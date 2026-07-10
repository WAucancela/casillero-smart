"""
infrastructure/zkteco/adms_router.py

Receptor del protocolo PUSH (ADMS) del ZKTeco SenseFace 2A.

CÓMO FUNCIONA:
  1. El SenseFace 2A se configura con la IP/puerto de este servidor.
  2. El dispositivo hace HTTP POST a /iclock/cdata cada vez que detecta un evento
     (acceso facial, huella, tarjeta, entrada/salida).
  3. Este endpoint recibe el evento, lo parsea, busca el usuario en la BD
     y dispara el flujo de apertura de cerradura si corresponde.
  4. El dispositivo también hace GET /iclock/getrequest para recibir comandos
     (agregar usuario, registrar plantilla biométrica, etc).

PROTOCOLO ADMS ZKTeco (texto plano, no JSON):
  El cuerpo del POST viene como texto con campos separados por tabulaciones:
    PIN\tTiempo\tEstado\tVerificacion\tWorkcode\n
  Ejemplo:
    1001\t2026-03-11 09:30:00\t0\t1\t0

REFERENCIA: ZKTeco Push SDK Protocol (ADMS) v2.x
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Request, Response, Depends, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database.conexion import get_db
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.acceso_repo import AccesoRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.database.terminal_repo import TerminalRepository
from infrastructure.hardware.cerradura_service import CerraduraService
from domain.entities.acceso_log import ResultadoAcceso
from domain.rules.reglas_acceso import ReglaAcceso
from config.settings import settings

logger = logging.getLogger(__name__)


def _ip_del_request(request: Request) -> str:
    return (request.headers.get("X-Real-IP") or request.client.host) if request else "desconocida"


def verificar_ip_permitida(request: Request) -> None:
    """
    Si ADMS_ALLOWED_IPS está configurado, rechaza cualquier request cuya IP
    de origen no esté en la lista. Vacío (default) = sin restricción por IP,
    para no romper instalaciones donde los terminales no tienen IP fija.
    """
    permitidas = [ip.strip() for ip in settings.ADMS_ALLOWED_IPS.split(",") if ip.strip()]
    if not permitidas:
        return
    if _ip_del_request(request) not in permitidas:
        logger.warning(f"[ZKTeco] Request rechazado por IP no permitida: {_ip_del_request(request)}")
        raise HTTPException(status_code=403, detail="IP no autorizada")


router = APIRouter(prefix="/iclock", tags=["ZKTeco ADMS"], dependencies=[Depends(verificar_ip_permitida)])

# ── Registro de terminales vistas (en memoria) ────────────────────────────────
# { SN: { "sn": str, "ip": str, "ultimo_contacto": datetime, "ultimo_evento": datetime|None } }
_terminales_vistas: dict[str, dict] = {}

# ── Mapa de códigos de verificación del ZKTeco ────────────────────────────────
VERIFY_MODE = {
    "0": "password",
    "1": "fingerprint",
    "2": "card",
    "3": "fingerprint_password",
    "4": "card_password",
    "6": "face",
    "10": "face_fingerprint",
    "11": "face_password",
    "12": "face_card",
    "200": "face",     # SenseFace 2A reporta 200 para reconocimiento facial
    "15":  "face",     # SenseFace 2A también reporta 15 en algunos firmware
}

# ── Mapa de estados (checkin / checkout / etc) ────────────────────────────────
STATUS_MAP = {
    "0": "check-in",
    "1": "check-out",
    "2": "break-out",
    "3": "break-in",
    "4": "overtime-in",
    "5": "overtime-out",
    "255": "access-control",  # SenseFace 2A usa 255 para control de acceso
}


# ── 1. HANDSHAKE inicial ───────────────────────────────────────────────────────
@router.get("/cdata")
async def handshake(
    SN: str,                        # Número de serie del dispositivo
    options: Optional[str] = None,  # ZKTeco solicita opciones del servidor
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    El ZKTeco hace GET /iclock/cdata?SN=XXXX al conectarse.
    El servidor responde con la configuración del dispositivo.
    """
    logger.info(f"[ZKTeco] Handshake del dispositivo SN={SN}")

    ip = (request.headers.get("X-Real-IP") or request.client.host) if request else "desconocida"
    try:
        await TerminalRepository(db).upsert(sn=SN, ip=ip)
    except Exception as e:
        logger.warning(f"[ZKTeco] No se pudo registrar terminal en BD: {e}")

    # Respuesta que el dispositivo ZKTeco espera (texto plano)
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    respuesta = (
        f"GET OPTION FROM: {SN}\n"
        f"ATTLOGStamp=None\n"
        f"OPERLOGStamp=9999\n"
        f"ATTPHOTOStamp=None\n"
        f"ErrorDelay=30\n"
        f"Delay=10\n"
        f"TransTimes=00:00;14:05\n"
        f"TransInterval=1\n"
        f"TransFlag=TransData AttLog OpLog AttPhoto\n"
        f"TimeZone=UTC-5\n"
        f"Realtime=1\n"
        f"Encrypt=None\n"
        f"ServerVer=2.4.1\n"
        f"PushProtVer=2.4.1\n"
        f"TableNameStamp=None\n"
        f"SvrMode=0\n"
        f"SN={SN}\n"
        f"date={ahora}\n"
    )
    return Response(content=respuesta, media_type="text/plain")


# ── 2. RECEPTOR de eventos (asistencia / acceso) ───────────────────────────────
@router.post("/cdata")
async def recibir_evento(
    request: Request,
    SN: str,                          # Número de serie del dispositivo
    table: Optional[str] = None,      # "ATTLOG" (asistencia) o "OPERLOG"
    Stamp: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    El ZKTeco POSTea aquí cada vez que registra un evento.
    El cuerpo es texto plano con líneas tab-separadas.
    
    Formato ATTLOG:
        PIN\\tTiempo\\tEstado\\tVerificacion\\tWorkcode\\tReserved\\n
    
    Ejemplo real SenseFace 2A:
        1001\\t2026-03-11 09:30:00\\t255\\t200\\t0\\t\\n
        PIN=1001, Tiempo=2026-03-11 09:30:00, Estado=255(access-control), Verify=200(face)
    """
    body = await request.body()
    body_text = body.decode("utf-8", errors="ignore").strip()

    logger.info(f"[ZKTeco] Evento recibido — SN={SN} table={table}")
    logger.debug(f"[ZKTeco] Body: {body_text!r}")

    if not body_text:
        return Response(content="OK\n", media_type="text/plain")

    # Solo procesar ATTLOG (eventos de acceso). OPERLOG son logs operativos del dispositivo.
    if table and table.upper() != "ATTLOG":
        logger.debug(f"[ZKTeco] Tabla '{table}' ignorada (solo se procesa ATTLOG)")
        return Response(content=f"OK: {Stamp or '0'}\n", media_type="text/plain")

    eventos_procesados = 0
    errores = 0

    for linea in body_text.splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            await _procesar_linea_attlog(linea, SN, db)
            eventos_procesados += 1
        except Exception as e:
            logger.error(f"[ZKTeco] Error procesando línea '{linea}': {e}")
            errores += 1

    logger.info(f"[ZKTeco] Procesados {eventos_procesados} eventos, {errores} errores")

    # ZKTeco espera "OK" o "OK: <stamp>" para confirmar recepción
    return Response(
        content=f"OK: {Stamp or '0'}\n",
        media_type="text/plain",
    )


# ── 3. COLA de comandos para el dispositivo ────────────────────────────────────
_comandos_pendientes: dict[str, list[str]] = {}  # SN → [comando1, comando2, ...]


@router.get("/getrequest")
async def obtener_comandos(SN: str, request: Request = None, db: AsyncSession = Depends(get_db)):
    """
    El ZKTeco hace polling aquí para recibir comandos del servidor:
    - Registrar nuevo usuario
    - Subir plantilla biométrica
    - Eliminar usuario
    - Abrir puerta remotamente
    
    Si no hay comandos, responde con "OK\n".
    """
    ip = (request.headers.get("X-Real-IP") or request.client.host) if request else "desconocida"
    try:
        await TerminalRepository(db).upsert(sn=SN, ip=ip)
    except Exception:
        pass  # No interrumpir el flujo de comandos por un error de BD

    comandos = _comandos_pendientes.pop(SN, [])
    if not comandos:
        return Response(content="OK\n", media_type="text/plain")

    # Enviar el primer comando (ZKTeco procesa uno por vez)
    cmd = comandos.pop(0)
    if comandos:
        _comandos_pendientes[SN] = comandos  # guardar el resto
    logger.info(f"[ZKTeco] Enviando comando a {SN}: {cmd!r}")
    return Response(content=cmd + "\n", media_type="text/plain")


@router.post("/devicecmd")
async def resultado_comando(SN: str, request: Request):
    """
    El ZKTeco reporta aquí el resultado de ejecutar un comando.
    Ejemplo: ID=1&Return=0&CMD=DATA UPDATE USERINFO PIN=1001...
    """
    body = await request.body()
    logger.info(f"[ZKTeco] Resultado de comando — SN={SN}: {body.decode()!r}")
    return Response(content="OK\n", media_type="text/plain")


# ── 4. SUBIDA de fotos de eventos ──────────────────────────────────────────────
@router.post("/cdata/photo")
async def recibir_foto(SN: str, request: Request):
    """
    Si el SenseFace 2A tiene habilitado 'Photo Capture',
    puede enviar la foto del evento junto con el registro.
    """
    body = await request.body()
    logger.info(f"[ZKTeco] Foto recibida del SN={SN}, tamaño={len(body)} bytes")
    # Aquí podrías guardar la foto en el sistema de archivos o S3
    # open(f"/tmp/zk_photo_{SN}_{datetime.now().timestamp()}.jpg", "wb").write(body)
    return Response(content="OK\n", media_type="text/plain")


# ── Helpers internos ───────────────────────────────────────────────────────────

async def _procesar_linea_attlog(linea: str, sn_dispositivo: str, db: AsyncSession):
    """
    Parsea una línea ATTLOG y ejecuta la lógica de acceso si corresponde.
    
    Formato: PIN\\tFecha\\tEstado\\tVerificacion\\tWorkcode\\tReserved
    """
    partes = linea.split("\t")
    if len(partes) < 2:
        logger.warning(f"[ZKTeco] Línea con formato inesperado: {linea!r}")
        return

    pin          = partes[0].strip()   # ID del usuario en el dispositivo
    timestamp_str= partes[1].strip()   # "2026-03-11 09:30:00"
    estado_cod   = partes[2].strip() if len(partes) > 2 else "0"
    verify_cod   = partes[3].strip() if len(partes) > 3 else "0"

    # Parsear timestamp
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        logger.warning(f"[ZKTeco] Timestamp inválido: {timestamp_str!r}")
        return

    modo_verificacion = VERIFY_MODE.get(verify_cod, f"desconocido({verify_cod})")
    tipo_evento       = STATUS_MAP.get(estado_cod, f"desconocido({estado_cod})")

    logger.info(
        f"[ZKTeco] Evento — PIN={pin} Hora={timestamp_str} "
        f"Modo={modo_verificacion} Tipo={tipo_evento}"
    )
    try:
        await TerminalRepository(db).upsert(sn=sn_dispositivo, ip="", ultimo_evento=timestamp)
    except Exception:
        pass

    # Solo procesar eventos de control de acceso (no asistencia pura)
    es_acceso = estado_cod in ("255", "0") or tipo_evento in ("check-in", "access-control")
    if not es_acceso:
        logger.debug(f"[ZKTeco] Evento de tipo '{tipo_evento}' omitido (no es acceso)")
        return

    # El dispositivo debe estar registrado y autorizado explícitamente por un
    # administrador antes de que sus eventos puedan abrir un casillero. Sin
    # este chequeo, cualquiera que conociera esta URL podía hacerse pasar por
    # un ZKTeco inventando un SN y un PIN válido.
    terminal = await TerminalRepository(db).obtener_por_sn(sn_dispositivo)
    if not terminal or not terminal.autorizado:
        logger.warning(f"[ZKTeco] Dispositivo SN={sn_dispositivo} no autorizado — evento de acceso rechazado")
        await _registrar_log(
            db, None, sn_dispositivo,
            ResultadoAcceso.DENEGADO_DISPOSITIVO_NO_AUTORIZADO,
            confianza=0.0,
        )
        return

    # Buscar usuario por PIN (el PIN del ZKTeco = usuario_id en nuestra BD)
    usuario_repo = UsuarioRepository(db)
    usuario = await usuario_repo.obtener_por_id(int(pin))

    if not usuario:
        logger.warning(f"[ZKTeco] Usuario con PIN={pin} no encontrado en BD")
        await _registrar_log(
            db, None, sn_dispositivo,
            ResultadoAcceso.DENEGADO_USUARIO_INACTIVO,
            confianza=0.0,
        )
        return

    # Aplicar reglas de acceso (el ZKTeco ya verificó biometría internamente)
    ok, resultado = ReglaAcceso.validar_usuario_activo(usuario)
    if ok:
        ok, resultado = ReglaAcceso.validar_horario_permitido(timestamp)

    casillero_id_log = None
    if resultado == ResultadoAcceso.EXITOSO:
        logger.info(f"[ZKTeco] ✅ Acceso aprobado para {usuario.nombre} {usuario.apellido}")

        # Auto-activar si estaba pendiente de biometría (primer acceso exitoso)
        from domain.entities.usuario import EstadoUsuario
        if usuario.estado == EstadoUsuario.PENDIENTE_BIOMETRIA:
            await usuario_repo.actualizar_estado(usuario.id, EstadoUsuario.ACTIVO)
            logger.info(f"[ZKTeco] Usuario {usuario.id} activado automáticamente tras primer acceso")

        casillero_repo = CasilleroRepository(db)
        casillero = await casillero_repo.obtener_por_usuario(usuario.id)
        if casillero:
            casillero_id_log = casillero.id
            CerraduraService().abrir(casillero)
            logger.info(f"[ZKTeco] 🔓 Casillero {casillero.numero} abierto para {usuario.nombre}")
        else:
            logger.warning(f"[ZKTeco] Usuario {usuario.id} no tiene casillero asignado")
    else:
        logger.warning(f"[ZKTeco] ❌ Acceso denegado — {resultado}")

    # Registrar log
    await _registrar_log(
        db, usuario.id, sn_dispositivo,
        resultado,
        confianza=1.0 if resultado == ResultadoAcceso.EXITOSO else 0.0,
        casillero_id=casillero_id_log,
    )


async def _registrar_log(
    db: AsyncSession,
    usuario_id: Optional[int],
    terminal_id: str,
    resultado: ResultadoAcceso,
    confianza: float,
    casillero_id: Optional[int] = None,
):
    """Guarda el evento en la tabla accesos_log."""
    from infrastructure.database.acceso_repo import AccesoRepository
    from domain.entities.acceso_log import AccesoLog
    repo = AccesoRepository(db)
    await repo.guardar(AccesoLog(
        id=None,
        usuario_id=usuario_id,
        casillero_id=casillero_id,
        terminal_id=terminal_id,
        resultado=resultado,
        confianza_biometrica=confianza,
    ))
    await db.commit()


# ── API para enviar comandos al dispositivo ────────────────────────────────────

def encolar_comando_usuario(sn: str, pin: int, nombre: str, privilegio: int = 0):
    """
    Registra un nuevo usuario en el SenseFace 2A.
    El dispositivo recogerá este comando en su próximo GET /iclock/getrequest.
    
    Uso:
        encolar_comando_usuario("AXHN12345678", pin=42, nombre="Ana García")
    """
    cmd = f"C:1:DATA UPDATE USERINFO PIN={pin}\tName={nombre}\tPrivilege={privilegio}\tPassword=\tCard=\tGroup=1\tTimeZone=0\tVerifyStyle=1\n"
    _comandos_pendientes.setdefault(sn, []).append(cmd)
    logger.info(f"[ZKTeco] Comando 'agregar usuario PIN={pin}' encolado para SN={sn}")


def encolar_eliminar_usuario(sn: str, pin: int):
    """
    Elimina un usuario del SenseFace 2A (p.ej. al dar de baja al empleado).
    """
    cmd = f"C:2:DATA DELETE USERINFO PIN={pin}\n"
    _comandos_pendientes.setdefault(sn, []).append(cmd)
    logger.info(f"[ZKTeco] Comando 'eliminar usuario PIN={pin}' encolado para SN={sn}")


def encolar_abrir_puerta(sn: str, tiempo_segundos: int = 5):
    """
    Ordena al SenseFace 2A abrir su relé de puerta directamente.
    Útil como respaldo si MQTT no responde.
    """
    cmd = f"C:3:CONTROL DEVICE 1,{tiempo_segundos * 1000},1,1,0\n"
    _comandos_pendientes.setdefault(sn, []).append(cmd)
    logger.info(f"[ZKTeco] Comando 'abrir puerta {tiempo_segundos}s' encolado para SN={sn}")
