import logging
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.database.casillero_repo import CasilleroRepository
from infrastructure.notificaciones.email_service import EmailService
from domain.entities.casillero import Casillero
from domain.rules.reglas_asignacion import ReglaAsignacion

logger = logging.getLogger(__name__)

class AsignarCasillero:
    """
    Caso de uso: asignar un casillero disponible a un usuario.
    Aplica las reglas de asignación y notifica al usuario.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        casillero_repo: CasilleroRepository,
        email_service: EmailService,
    ):
        self.usuario_repo = usuario_repo
        self.casillero_repo = casillero_repo
        self.email_service = email_service

    async def ejecutar(self, usuario_id: int) -> Casillero:
        # 1. Obtener usuario
        usuario = await self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario no encontrado: {usuario_id}")

        # 2. Verificar que el usuario puede recibir casillero (regla de dominio)
        puede, razon = ReglaAsignacion.usuario_puede_recibir_casillero(usuario)
        if not puede:
            raise ValueError(razon)

        # 3. Verificar que no tenga ya un casillero
        casillero_existente = await self.casillero_repo.obtener_por_usuario(usuario_id)
        if casillero_existente:
            raise ValueError(f"El usuario ya tiene el casillero {casillero_existente.numero}")

        # 4. Obtener casilleros disponibles y seleccionar el mejor
        disponibles = await self.casillero_repo.listar_disponibles()
        casillero = ReglaAsignacion.seleccionar_mejor_casillero(disponibles, usuario)
        if not casillero:
            raise ValueError("No hay casilleros disponibles en este momento")

        # 5. Asignar
        casillero.asignar(usuario_id)
        await self.casillero_repo.actualizar_asignacion(casillero)
        logger.info(f"Casillero {casillero.numero} asignado a usuario {usuario_id}")

        # 6. Notificar
        self.email_service.notificar_casillero_asignado(
            usuario.email,
            usuario.nombre_completo,
            casillero.numero,
            casillero.piso,
        )
        return casillero
