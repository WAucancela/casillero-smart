from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Boolean, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from infrastructure.database.conexion import Base


class TerminalZKTecoModel(Base):
    __tablename__ = "terminales_zkteco"
    __table_args__ = {"extend_existing": True}

    id             = Column(Integer, primary_key=True, autoincrement=True)
    sn             = Column(String(100), unique=True, nullable=False, index=True)
    ip             = Column(String(50),  nullable=True)
    descripcion    = Column(String(200), nullable=True)
    piso           = Column(Integer,     nullable=True, default=1)
    activo         = Column(Boolean,     default=True)
    ultimo_contacto = Column(DateTime,   nullable=True)
    ultimo_evento   = Column(DateTime,   nullable=True)


class TerminalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, sn: str, ip: str, ultimo_evento: Optional[datetime] = None):
        """Inserta o actualiza una terminal por SN."""
        ahora = datetime.now()
        stmt = pg_insert(TerminalZKTecoModel).values(
            sn=sn,
            ip=ip,
            ultimo_contacto=ahora,
            **({"ultimo_evento": ultimo_evento} if ultimo_evento else {}),
        ).on_conflict_do_update(
            index_elements=["sn"],
            set_={
                "ip": ip,
                "ultimo_contacto": ahora,
                **({"ultimo_evento": ultimo_evento} if ultimo_evento else {}),
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def listar(self) -> List[TerminalZKTecoModel]:
        result = await self.db.execute(select(TerminalZKTecoModel).order_by(TerminalZKTecoModel.id))
        return result.scalars().all()

    async def obtener_por_id(self, terminal_id: int) -> Optional[TerminalZKTecoModel]:
        result = await self.db.execute(
            select(TerminalZKTecoModel).where(TerminalZKTecoModel.id == terminal_id)
        )
        return result.scalar_one_or_none()
