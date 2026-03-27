import logging
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.database.acceso_repo import AccesoRepository
from infrastructure.biometria.motor_facial import MotorFacial
from infrastructure.biometria.encriptacion_vectores import EncriptacionVectores
from infrastructure.hardware.cerradura_service import CerraduraService
from infrastructure.notificaciones.email_service import EmailService
from infrastructure.database.conexion import Base
from application.usuarios.registrar_biometria import BiometriaModel
from domain.rules.reglas_acceso import ReglaAcceso
from domain.entities.acceso_log import AccesoLog, ResultadoAcceso
from config.settings import settings

logger = logging.getLogger(__name__)

LIMITE_INTENTOS_ALERTA = 5

@dataclass
class SolicitudAccesoDTO:
    imagen_base64: str
    terminal_id: str

@dataclass
class ResultadoAccesoDTO:
    permitido: bool
    resultado: ResultadoAcceso
    casillero_numero: str | None = None
    mensaje: str = ""

class ValidarAcceso:
    """
    Caso de uso principal: valida un intento de acceso biométrico.
    Es el flujo más crítico del sistema.
    """

    def __init__(
        self,
        db: AsyncSession,
        usuario_repo: UsuarioRepository,
        casillero_repo: CasilleroRepository,
        acceso_repo: AccesoRepository,
        motor_facial: MotorFacial,
        encriptacion: EncriptacionVectores,
        cerradura_service: CerraduraService,
        email_service: EmailService,
    ):
        self.db = db
        self.usuario_repo = usuario_repo
        self.casillero_repo = casillero_repo
        self.acceso_repo = acceso_repo
        self.motor_facial = motor_facial
        self.encriptacion = encriptacion
        self.cerradura_service = cerradura_service
        self.email_service = email_service

    async def ejecutar(self, solicitud: SolicitudAccesoDTO) -> ResultadoAccesoDTO:
        # 1. Generar vector del rostro capturado
        vector_entrada = self.motor_facial.generar_vector_desde_imagen(
            solicitud.imagen_base64
        )
        if not vector_entrada:
            await self._registrar_log(None, None, solicitud.terminal_id,
                                       ResultadoAcceso.DENEGADO_BIOMETRIA, 0.0)
            return ResultadoAccesoDTO(False, ResultadoAcceso.DENEGADO_BIOMETRIA,
                                      mensaje="No se detectó un rostro válido")

        # 2. Cargar todos los vectores biométricos activos
        result = await self.db.execute(select(BiometriaModel))
        registros = result.scalars().all()
        vectores_candidatos = [
            (r.usuario_id, self.encriptacion.desencriptar(r.vector_encriptado))
            for r in registros
        ]

        # 3. Comparar contra todos los vectores
        match = self.motor_facial.comparar_con_multiples_vectores(
            vector_entrada, vectores_candidatos
        )
        if not match:
            await self._registrar_log(None, None, solicitud.terminal_id,
                                       ResultadoAcceso.DENEGADO_BIOMETRIA, 0.0)
            return ResultadoAccesoDTO(False, ResultadoAcceso.DENEGADO_BIOMETRIA,
                                      mensaje="Rostro no reconocido")

        usuario_id, score = match

        # 4. Cargar usuario y casillero
        usuario = await self.usuario_repo.obtener_por_id(usuario_id)
        casillero = await self.casillero_repo.obtener_por_usuario(usuario_id)

        if not casillero:
            await self._registrar_log(usuario_id, None, solicitud.terminal_id,
                                       ResultadoAcceso.DENEGADO_SIN_CASILLERO, score)
            return ResultadoAccesoDTO(False, ResultadoAcceso.DENEGADO_SIN_CASILLERO,
                                      mensaje="Usuario sin casillero asignado")

        # 5. Ejecutar todas las reglas de acceso
        permitido, resultado = ReglaAcceso.ejecutar_todas_las_validaciones(
            score, usuario, casillero
        )

        # 6. Registrar log
        await self._registrar_log(usuario_id, casillero.id,
                                   solicitud.terminal_id, resultado, score)

        if not permitido:
            await self._verificar_alerta_seguridad(solicitud.terminal_id)
            return ResultadoAccesoDTO(False, resultado,
                                      mensaje=f"Acceso denegado: {resultado.value}")

        # 7. Abrir cerradura
        self.cerradura_service.abrir(casillero)
        logger.info(
            f"Acceso exitoso: usuario={usuario_id} "
            f"casillero={casillero.numero} score={score:.2f}"
        )
        return ResultadoAccesoDTO(
            True, ResultadoAcceso.EXITOSO,
            casillero_numero=casillero.numero,
            mensaje=f"Bienvenido {usuario.nombre}"
        )

    async def _registrar_log(
        self, usuario_id, casillero_id, terminal_id, resultado, score
    ):
        log = AccesoLog(
            id=None,
            usuario_id=usuario_id,
            casillero_id=casillero_id,
            terminal_id=terminal_id,
            resultado=resultado,
            confianza_biometrica=score,
        )
        await self.acceso_repo.guardar(log)

    async def _verificar_alerta_seguridad(self, terminal_id: str):
        intentos = await self.acceso_repo.contar_intentos_fallidos_recientes(terminal_id)
        if intentos >= LIMITE_INTENTOS_ALERTA:
            self.email_service.notificar_acceso_denegado_repetido(
                settings.SMTP_USER,
                terminal_id,
                intentos
            )
