"""
infrastructure/zkteco/dispositivo_service.py

Servicio de gestión del SenseFace 2A.
Permite sincronizar usuarios, plantillas biométricas y obtener estado.

NOTA: El SenseFace 2A se gestiona a través de dos vías:
  1. PUSH (ADMS): el dispositivo envía eventos → adms_router.py
  2. Comandos vía cola: el servidor encola comandos → adms_router.py (getrequest)
  
Para comandos en tiempo real también se puede usar el API HTTP del dispositivo
si está habilitado el acceso HTTPS/SSH backend (opción en firmware del SenseFace 2A).
"""

import logging
import httpx
from typing import Optional
from dataclasses import dataclass

from infrastructure.zkteco.adms_router import (
    encolar_comando_usuario,
    encolar_eliminar_usuario,
    encolar_abrir_puerta,
)

logger = logging.getLogger(__name__)


@dataclass
class InfoDispositivo:
    sn: str
    ip: str
    firmware: Optional[str] = None
    usuarios_registrados: Optional[int] = None
    capacidad_maxima: int = 3000
    en_linea: bool = False


class DispositivoZKTeco:
    """
    Gestiona la comunicación con un SenseFace 2A específico.
    
    Uso:
        dispositivo = DispositivoZKTeco(sn="AXHN12345678", ip="192.168.1.50")
        await dispositivo.registrar_usuario(pin=42, nombre="Ana García")
        await dispositivo.dar_baja_usuario(pin=42)
        await dispositivo.abrir_puerta()
    """

    def __init__(self, sn: str, ip: str, puerto: int = 80, timeout: int = 5):
        self.sn      = sn
        self.ip      = ip
        self.puerto  = puerto
        self.timeout = timeout
        self._base   = f"http://{ip}:{puerto}"

    # ── Gestión de usuarios ────────────────────────────────────────────────────

    async def registrar_usuario(
        self,
        pin: int,
        nombre: str,
        privilegio: int = 0,
    ) -> bool:
        """
        Registra un usuario en el SenseFace 2A.
        El reconocimiento facial se hace directamente en el dispositivo.
        
        Args:
            pin: ID del usuario (debe coincidir con usuario_id en nuestra BD)
            nombre: Nombre a mostrar en la pantalla del dispositivo
            privilegio: 0=usuario normal, 14=administrador
        """
        try:
            encolar_comando_usuario(self.sn, pin, nombre, privilegio)
            logger.info(f"[ZKTeco] Usuario PIN={pin} registrado en cola para SN={self.sn}")
            return True
        except Exception as e:
            logger.error(f"[ZKTeco] Error registrando usuario PIN={pin}: {e}")
            return False

    async def dar_baja_usuario(self, pin: int) -> bool:
        """
        Elimina un usuario del dispositivo.
        Llamar cuando se dé de baja al empleado.
        """
        try:
            encolar_eliminar_usuario(self.sn, pin)
            logger.info(f"[ZKTeco] Usuario PIN={pin} marcado para eliminar en SN={self.sn}")
            return True
        except Exception as e:
            logger.error(f"[ZKTeco] Error eliminando usuario PIN={pin}: {e}")
            return False

    async def abrir_puerta(self, segundos: int = 5) -> bool:
        """
        Activa el relé del SenseFace 2A para abrir la puerta directamente.
        Útil como respaldo al MQTT o para terminales standalone.
        """
        try:
            encolar_abrir_puerta(self.sn, segundos)
            logger.info(f"[ZKTeco] Apertura de puerta ({segundos}s) encolada para SN={self.sn}")
            return True
        except Exception as e:
            logger.error(f"[ZKTeco] Error encolando apertura de puerta: {e}")
            return False

    # ── Estado del dispositivo (vía HTTP directo) ──────────────────────────────

    async def ping(self) -> bool:
        """Verifica si el dispositivo responde en la red."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(f"{self._base}/iclock/cdata?SN={self.sn}&options=")
                return r.status_code in (200, 400)
        except Exception:
            return False

    async def obtener_info(self) -> Optional[InfoDispositivo]:
        """
        Obtiene información básica del dispositivo via HTTP.
        Requiere que el acceso HTTPS/SSH backend esté habilitado en el firmware.
        """
        try:
            en_linea = await self.ping()
            return InfoDispositivo(
                sn=self.sn,
                ip=self.ip,
                en_linea=en_linea,
            )
        except Exception as e:
            logger.error(f"[ZKTeco] Error obteniendo info de SN={self.sn}: {e}")
            return None

    async def sincronizar_hora(self) -> bool:
        """
        Sincroniza la hora del dispositivo con el servidor.
        Importante para que los timestamps de los eventos sean correctos.
        """
        from datetime import datetime
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cmd = f"C:99:SET OPTION Date={ahora}\n"
        from infrastructure.zkteco.adms_router import _comandos_pendientes
        _comandos_pendientes.setdefault(self.sn, []).append(cmd)
        logger.info(f"[ZKTeco] Hora sincronizada para SN={self.sn}: {ahora}")
        return True


# ── Registro global de dispositivos ───────────────────────────────────────────

class RegistroDispositivos:
    """
    Mantiene el registro de todos los SenseFace 2A activos.
    
    Uso en main.py:
        from infrastructure.zkteco.dispositivo_service import registro_dispositivos
        registro_dispositivos.agregar("AXHN12345678", ip="192.168.1.50")
    """

    def __init__(self):
        self._dispositivos: dict[str, DispositivoZKTeco] = {}

    def agregar(self, sn: str, ip: str, puerto: int = 80) -> DispositivoZKTeco:
        d = DispositivoZKTeco(sn=sn, ip=ip, puerto=puerto)
        self._dispositivos[sn] = d
        logger.info(f"[ZKTeco] Dispositivo registrado: SN={sn} IP={ip}")
        return d

    def obtener(self, sn: str) -> Optional[DispositivoZKTeco]:
        return self._dispositivos.get(sn)

    def todos(self) -> list[DispositivoZKTeco]:
        return list(self._dispositivos.values())

    async def ping_todos(self) -> dict[str, bool]:
        resultados = {}
        for sn, d in self._dispositivos.items():
            resultados[sn] = await d.ping()
        return resultados


# Instancia global (singleton)
registro_dispositivos = RegistroDispositivos()
