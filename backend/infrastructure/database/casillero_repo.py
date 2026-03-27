from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime, select
from datetime import datetime
from typing import Optional, List

from infrastructure.database.conexion import Base
from domain.entities.casillero import Casillero, EstadoCasillero

class CasilleroModel(Base):
    __tablename__ = "casilleros"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), unique=True, nullable=False)
    piso = Column(Integer, nullable=False)
    zona = Column(String(50), nullable=False)
    controlador_id = Column(String(100), nullable=False)
    puerto_controlador = Column(Integer, nullable=False)
    estado = Column(SAEnum(EstadoCasillero, name='estado_casillero', create_type=False, values_callable=lambda x: [e.value for e in x]), default=EstadoCasillero.LIBRE)
    usuario_asignado_id = Column(Integer, nullable=True)
    fecha_asignacion = Column(DateTime, nullable=True)

class CasilleroRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: CasilleroModel) -> Casillero:
        return Casillero(
            id=model.id,
            numero=model.numero,
            piso=model.piso,
            zona=model.zona,
            controlador_id=model.controlador_id,
            puerto_controlador=model.puerto_controlador,
            estado=model.estado,
            usuario_asignado_id=model.usuario_asignado_id,
            fecha_asignacion=model.fecha_asignacion,
        )

    async def listar_disponibles(self) -> List[Casillero]:
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.estado == EstadoCasillero.LIBRE)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def obtener_por_id(self, casillero_id: int) -> Optional[Casillero]:
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.id == casillero_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def obtener_por_usuario(self, usuario_id: int) -> Optional[Casillero]:
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.usuario_asignado_id == usuario_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def actualizar_asignacion(self, casillero: Casillero):
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.id == casillero.id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.estado = casillero.estado
            model.usuario_asignado_id = casillero.usuario_asignado_id
            model.fecha_asignacion = casillero.fecha_asignacion
            await self.db.flush()

    async def listar_todos(self) -> List[Casillero]:
        result = await self.db.execute(select(CasilleroModel))
        return [self._to_entity(m) for m in result.scalars().all()]

    async def crear(self, casillero: Casillero) -> Casillero:
        model = CasilleroModel(
            numero=casillero.numero,
            piso=casillero.piso,
            zona=casillero.zona,
            controlador_id=casillero.controlador_id,
            puerto_controlador=casillero.puerto_controlador,
            estado=EstadoCasillero.LIBRE,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def eliminar(self, casillero_id: int) -> bool:
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.id == casillero_id)
        )
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.db.delete(model)
        await self.db.flush()
        return True

    async def cambiar_estado(self, casillero_id: int, estado: EstadoCasillero):
        result = await self.db.execute(
            select(CasilleroModel).where(CasilleroModel.id == casillero_id)
        )
        model = result.scalar_one_or_none()
        if model:
            model.estado = estado
            await self.db.flush()
