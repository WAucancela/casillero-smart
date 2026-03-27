import logging
from infrastructure.database.casillero_repo import CasilleroRepository

logger = logging.getLogger(__name__)

class LiberarCasillero:
    """
    Caso de uso: liberar el casillero asignado a un usuario.
    """

    def __init__(self, casillero_repo: CasilleroRepository):
        self.casillero_repo = casillero_repo

    async def ejecutar(self, usuario_id: int) -> str:
        casillero = await self.casillero_repo.obtener_por_usuario(usuario_id)
        if not casillero:
            raise ValueError(f"El usuario {usuario_id} no tiene casillero asignado")

        numero = casillero.numero
        casillero.liberar()
        await self.casillero_repo.actualizar_asignacion(casillero)
        logger.info(f"Casillero {numero} liberado del usuario {usuario_id}")
        return numero
