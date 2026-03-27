import logging
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from domain.entities.casillero import Casillero
from domain.rules.reglas_asignacion import ReglaAsignacion

logger = logging.getLogger(__name__)

class AsignarCasilleroManual:
    """
    Caso de uso: asignar un casillero específico (elegido por el admin) a un usuario.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        casillero_repo: CasilleroRepository,
    ):
        self.usuario_repo = usuario_repo
        self.casillero_repo = casillero_repo

    async def ejecutar(self, usuario_id: int, casillero_id: int) -> Casillero:
        # 1. Verificar usuario
        usuario = await self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario no encontrado: {usuario_id}")

        puede, razon = ReglaAsignacion.usuario_puede_recibir_casillero(usuario)
        if not puede:
            raise ValueError(razon)

        # 2. Verificar que no tenga ya uno asignado
        existente = await self.casillero_repo.obtener_por_usuario(usuario_id)
        if existente:
            raise ValueError(f"El usuario ya tiene el casillero {existente.numero} asignado")

        # 3. Verificar casillero disponible
        casillero = await self.casillero_repo.obtener_por_id(casillero_id)
        if not casillero:
            raise ValueError(f"Casillero no encontrado: {casillero_id}")
        if not casillero.esta_disponible():
            raise ValueError(f"El casillero {casillero.numero} no está disponible")

        # 4. Asignar
        casillero.asignar(usuario_id)
        await self.casillero_repo.actualizar_asignacion(casillero)
        logger.info(f"Casillero {casillero.numero} asignado manualmente a usuario {usuario_id}")
        return casillero
