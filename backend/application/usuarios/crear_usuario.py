import logging
from dataclasses import dataclass
from domain.entities.usuario import Usuario, EstadoUsuario
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.notificaciones.email_service import EmailService

logger = logging.getLogger(__name__)

@dataclass
class CrearUsuarioDTO:
    nombre: str
    apellido: str
    email: str
    departamento: str
    piso_preferido: int | None = None

class CrearUsuario:
    """
    Caso de uso: crear un nuevo usuario en el sistema.
    Coordina la validación, persistencia y notificación.
    """

    def __init__(
        self,
        usuario_repo: UsuarioRepository,
        email_service: EmailService
    ):
        self.usuario_repo = usuario_repo
        self.email_service = email_service

    async def ejecutar(self, datos: CrearUsuarioDTO) -> Usuario:
        # 1. Verificar que el email no exista ya
        existente = await self.usuario_repo.obtener_por_email(datos.email)
        if existente:
            raise ValueError(f"Ya existe un usuario con el email: {datos.email}")

        # 2. Crear la entidad
        usuario = Usuario(
            id=None,
            nombre=datos.nombre,
            apellido=datos.apellido,
            email=datos.email,
            departamento=datos.departamento,
            piso_preferido=datos.piso_preferido,
            estado=EstadoUsuario.PENDIENTE_BIOMETRIA,
        )

        # 3. Persistir
        usuario_guardado = await self.usuario_repo.guardar(usuario)
        logger.info(f"Usuario creado: {usuario_guardado.email} (id={usuario_guardado.id})")

        return usuario_guardado
