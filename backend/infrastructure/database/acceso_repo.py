from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, Float, Enum as SAEnum, DateTime, select
from datetime import datetime, timedelta
from typing import List, Optional

from infrastructure.database.conexion import Base
from domain.entities.acceso_log import AccesoLog, ResultadoAcceso

class AccesoLogModel(Base):
    __tablename__ = "accesos_log"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, nullable=True, index=True)
    casillero_id = Column(Integer, nullable=True, index=True)
    terminal_id = Column(String(100), nullable=False)
    resultado = Column(SAEnum(ResultadoAcceso, name="resultado_acceso", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False)
    confianza_biometrica = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    detalle = Column(String(500), nullable=True)

class AccesoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: AccesoLogModel) -> AccesoLog:
        return AccesoLog(
            id=model.id,
            usuario_id=model.usuario_id,
            casillero_id=model.casillero_id,
            terminal_id=model.terminal_id,
            resultado=model.resultado,
            confianza_biometrica=model.confianza_biometrica,
            timestamp=model.timestamp,
            detalle=model.detalle,
        )

    async def guardar(self, log: AccesoLog) -> AccesoLog:
        model = AccesoLogModel(
            usuario_id=log.usuario_id,
            casillero_id=log.casillero_id,
            terminal_id=log.terminal_id,
            resultado=log.resultado,
            confianza_biometrica=log.confianza_biometrica,
            timestamp=log.timestamp,
            detalle=log.detalle,
        )
        self.db.add(model)
        await self.db.flush()
        return self._to_entity(model)

    async def listar_por_usuario(
        self, usuario_id: int, limite: int = 50
    ) -> List[AccesoLog]:
        result = await self.db.execute(
            select(AccesoLogModel)
            .where(AccesoLogModel.usuario_id == usuario_id)
            .order_by(AccesoLogModel.timestamp.desc())
            .limit(limite)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def listar_por_rango_fechas(
        self,
        desde: datetime,
        hasta: datetime,
        usuario_id: Optional[int] = None,
        resultado: Optional[str] = None,
    ) -> List[AccesoLog]:
        query = select(AccesoLogModel).where(
            AccesoLogModel.timestamp.between(desde, hasta)
        )
        if usuario_id:
            query = query.where(AccesoLogModel.usuario_id == usuario_id)
        if resultado:
            query = query.where(AccesoLogModel.resultado == resultado)
        query = query.order_by(AccesoLogModel.timestamp.desc())
        result = await self.db.execute(query)
        return [self._to_entity(m) for m in result.scalars().all()]

    async def contar_intentos_fallidos_recientes(
        self, terminal_id: str, minutos: int = 5
    ) -> int:
        desde = datetime.now() - timedelta(minutes=minutos)
        result = await self.db.execute(
            select(AccesoLogModel).where(
                AccesoLogModel.terminal_id == terminal_id,
                AccesoLogModel.resultado == ResultadoAcceso.DENEGADO_BIOMETRIA,
                AccesoLogModel.timestamp >= desde,
            )
        )
        return len(result.scalars().all())
