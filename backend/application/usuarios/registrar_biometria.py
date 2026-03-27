import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, select

from infrastructure.database.conexion import Base
from infrastructure.database.usuario_repo import UsuarioRepository
from infrastructure.biometria.motor_facial import MotorFacial
from infrastructure.biometria.encriptacion_vectores import EncriptacionVectores
from infrastructure.notificaciones.email_service import EmailService
from domain.entities.usuario import EstadoUsuario

logger = logging.getLogger(__name__)

class BiometriaModel(Base):
    __tablename__ = "biometria"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, nullable=False, unique=True, index=True)
    vector_encriptado = Column(String(5000), nullable=False)

class RegistrarBiometria:
    """
    Caso de uso: capturar y registrar el vector facial de un usuario.
    Coordina el motor facial, la encriptación y la persistencia.
    """

    def __init__(
        self,
        db: AsyncSession,
        usuario_repo: UsuarioRepository,
        motor_facial: MotorFacial,
        encriptacion: EncriptacionVectores,
        email_service: EmailService,
    ):
        self.db = db
        self.usuario_repo = usuario_repo
        self.motor_facial = motor_facial
        self.encriptacion = encriptacion
        self.email_service = email_service

    async def ejecutar(self, usuario_id: int, imagen_base64: str) -> bool:
        # 1. Verificar que el usuario existe
        usuario = await self.usuario_repo.obtener_por_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario no encontrado: {usuario_id}")

        # 2. Generar vector facial desde la imagen
        vector = self.motor_facial.generar_vector_desde_imagen(imagen_base64)
        if not vector:
            raise ValueError("No se pudo detectar un rostro válido en la imagen")

        # 3. Encriptar el vector
        vector_encriptado = self.encriptacion.encriptar(vector)

        # 4. Guardar o actualizar en BD
        result = await self.db.execute(
            select(BiometriaModel).where(BiometriaModel.usuario_id == usuario_id)
        )
        registro = result.scalar_one_or_none()

        if registro:
            registro.vector_encriptado = vector_encriptado
        else:
            self.db.add(BiometriaModel(
                usuario_id=usuario_id,
                vector_encriptado=vector_encriptado
            ))

        # 5. Activar el usuario
        await self.usuario_repo.actualizar_estado(usuario_id, EstadoUsuario.ACTIVO)
        logger.info(f"Biometría registrada para usuario_id={usuario_id}")

        # 6. Notificar al usuario
        self.email_service.notificar_registro_biometria(
            usuario.email,
            usuario.nombre_completo
        )
        return True
