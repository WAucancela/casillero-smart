from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum, select
from datetime import datetime
from typing import Optional, List
from infrastructure.database.conexion import Base


class AdministradorModel(Base):
    __tablename__ = "administradores"

    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String(100), nullable=False)
    apellido      = Column(String(100), nullable=False)
    email         = Column(String(200), unique=True, nullable=False, index=True)
    password_hash = Column(String(500), nullable=False)
    rol           = Column(
        SAEnum("superadmin", "admin", "viewer", name="rol_admin", create_type=False),
        nullable=False, default="admin"
    )
    activo        = Column(Boolean, default=True)
    ultimo_acceso = Column(DateTime, nullable=True)


class AdministradorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def buscar_por_email(self, email: str) -> Optional[AdministradorModel]:
        result = await self.db.execute(
            select(AdministradorModel).where(AdministradorModel.email == email)
        )
        return result.scalar_one_or_none()

    async def buscar_por_id(self, admin_id: int) -> Optional[AdministradorModel]:
        result = await self.db.execute(
            select(AdministradorModel).where(AdministradorModel.id == admin_id)
        )
        return result.scalar_one_or_none()

    async def listar_todos(self) -> List[AdministradorModel]:
        result = await self.db.execute(
            select(AdministradorModel).order_by(AdministradorModel.id)
        )
        return result.scalars().all()

    async def crear(self, nombre: str, apellido: str, email: str,
                    password_hash: str, rol: str) -> AdministradorModel:
        model = AdministradorModel(
            nombre=nombre, apellido=apellido, email=email,
            password_hash=password_hash, rol=rol, activo=True,
        )
        self.db.add(model)
        await self.db.flush()
        return model

    async def actualizar_rol(self, admin_id: int, rol: str):
        model = await self.buscar_por_id(admin_id)
        if model:
            model.rol = rol
            await self.db.flush()

    async def cambiar_activo(self, admin_id: int, activo: bool):
        model = await self.buscar_por_id(admin_id)
        if model:
            model.activo = activo
            await self.db.flush()

    async def actualizar_ultimo_acceso(self, admin_id: int):
        model = await self.buscar_por_id(admin_id)
        if model:
            model.ultimo_acceso = datetime.now()
            await self.db.flush()
