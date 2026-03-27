import logging
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository

logger = logging.getLogger(__name__)

class EliminarUsuario:
    """
    Caso de uso: eliminar permanentemente un usuario y liberar sus recursos.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        casillero_repo: CasilleroRepository,
    ):
        self.usuario_repo = usuario_repo
        self.casillero_repo = casillero_repo

    async def ejecutar(self, usuario_id: int) -> bool:
        # 1. Verificar que existe
        usuario = await self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario no encontrado: {usuario_id}")

        # 2. Liberar su casillero si tenía uno
        casillero = await self.casillero_repo.obtener_por_usuario(usuario_id)
        if casillero:
            casillero.liberar()
            await self.casillero_repo.actualizar_asignacion(casillero)
            logger.info(f"Casillero {casillero.numero} liberado antes de eliminar usuario {usuario_id}")

        # 3. Eliminar permanentemente
        await self.usuario_repo.eliminar(usuario_id)
        logger.info(f"Usuario {usuario_id} eliminado permanentemente")

        return True
