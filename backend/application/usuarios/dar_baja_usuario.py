import logging
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from domain.entities.usuario import EstadoUsuario

logger = logging.getLogger(__name__)

class DarBajaUsuario:
    """
    Caso de uso: desactivar un usuario y liberar todos sus recursos.
    Coordina tres acciones en secuencia: desactivar, liberar casillero.
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
            logger.info(f"Casillero {casillero.numero} liberado (usuario {usuario_id} dado de baja)")

        # 3. Desactivar el usuario
        await self.usuario_repo.actualizar_estado(usuario_id, EstadoUsuario.INACTIVO)
        logger.info(f"Usuario {usuario_id} dado de baja")

        return True
