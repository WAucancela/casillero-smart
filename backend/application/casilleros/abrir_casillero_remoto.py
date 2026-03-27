import logging
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.hardware.cerradura_service import CerraduraService
from infrastructure.database.acceso_repo import AccesoRepository
from domain.entities.acceso_log import AccesoLog, ResultadoAcceso

logger = logging.getLogger(__name__)

class AbrirCasilleroRemoto:
    """
    Caso de uso: un administrador abre un casillero manualmente desde el panel.
    Verifica que el casillero existe y envía la orden al hardware.
    """

    def __init__(
        self,
        casillero_repo: CasilleroRepository,
        cerradura_service: CerraduraService,
        acceso_repo: AccesoRepository,
    ):
        self.casillero_repo = casillero_repo
        self.cerradura_service = cerradura_service
        self.acceso_repo = acceso_repo

    async def ejecutar(self, casillero_id: int, admin_id: int) -> bool:
        # 1. Obtener casillero
        casillero = await self.casillero_repo.obtener_por_id(casillero_id)
        if not casillero:
            raise ValueError(f"Casillero no encontrado: {casillero_id}")

        # 2. Enviar orden al hardware
        enviado = self.cerradura_service.abrir(casillero)

        # 3. Registrar el log con apertura remota
        log = AccesoLog(
            id=None,
            usuario_id=None,
            casillero_id=casillero_id,
            terminal_id=f"admin:{admin_id}",
            resultado=ResultadoAcceso.EXITOSO if enviado else ResultadoAcceso.ERROR_HARDWARE,
            confianza_biometrica=None,
            detalle="Apertura remota por administrador"
        )
        await self.acceso_repo.guardar(log)

        logger.info(
            f"Apertura remota: casillero {casillero.numero} "
            f"por admin_id={admin_id} | enviado={enviado}"
        )
        return enviado
