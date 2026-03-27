from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime, select
from sqlalchemy.orm import mapped_column
from datetime import datetime
from typing import Optional, List

from infrastructure.database.conexion import Base
from domain.entities.usuario import Usuario, EstadoUsuario

class UsuarioModel(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    departamento = Column(String(100), nullable=False)
    piso_preferido = Column(Integer, nullable=True)
    estado = Column(SAEnum(EstadoUsuario, name='estado_usuario', create_type=False, values_callable=lambda x: [e.value for e in x]), default=EstadoUsuario.PENDIENTE_BIOMETRIA)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, nullable=True)

class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: UsuarioModel) -> Usuario:
        return Usuario(
            id=model.id,
            nombre=model.nombre,
            apellido=model.apellido,
            email=model.email,
            departamento=model.departamento,
            piso_preferido=model.piso_preferido,
            estado=model.estado,
            fecha_creacion=model.fecha_creacion,
            fecha_actualizacion=model.fecha_actualizacion,
        )

    async def guardar(self, usuario: Usuario) -> Usuario:
        model = UsuarioModel(
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            email=usuario.email,
            departamento=usuario.departamento,
            piso_preferido=usuario.piso_preferido,
            estado=usuario.estado,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def obtener_por_id(self, usuario_id: int) -> Optional[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def obtener_por_email(self, email: str) -> Optional[Usuario]:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.email == email)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def listar_todos(self) -> List[Usuario]:
        result = await self.db.execute(select(UsuarioModel))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def actualizar_estado(self, usuario_id: int, estado: EstadoUsuario):
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.estado = estado
            model.fecha_actualizacion = datetime.now()
            await self.db.flush()

    async def eliminar(self, usuario_id: int) -> bool:
        result = await self.db.execute(
            select(UsuarioModel).where(UsuarioModel.id == usuario_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.db.delete(model)
        await self.db.flush()
        return True
