"""
seed_data.py
Script para poblar la base de datos con datos de prueba realistas.
Ejecutar solo en entornos de desarrollo/testing.

Uso:
    python seeds/seed_data.py
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from passlib.context import CryptContext

import os
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://casilleros_user:password@localhost:5432/casilleros")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ── Datos de prueba ────────────────────────────────────────────────────────────

CONTROLADORES = [
    {"id": "ctrl-p1-a", "descripcion": "Controlador Piso 1 Zona A", "piso": 1, "zona": "A", "ip_local": "192.168.1.10"},
    {"id": "ctrl-p1-b", "descripcion": "Controlador Piso 1 Zona B", "piso": 1, "zona": "B", "ip_local": "192.168.1.11"},
    {"id": "ctrl-p2-a", "descripcion": "Controlador Piso 2 Zona A", "piso": 2, "zona": "A", "ip_local": "192.168.1.20"},
    {"id": "ctrl-p2-b", "descripcion": "Controlador Piso 2 Zona B", "piso": 2, "zona": "B", "ip_local": "192.168.1.21"},
    {"id": "ctrl-p3-a", "descripcion": "Controlador Piso 3 Zona A", "piso": 3, "zona": "A", "ip_local": "192.168.1.30"},
]

TERMINALES = [
    {"id": "term-p1-entrada", "descripcion": "Terminal Piso 1 Entrada", "piso": 1, "ubicacion": "Pasillo principal piso 1", "ip_local": "192.168.1.50"},
    {"id": "term-p2-entrada", "descripcion": "Terminal Piso 2 Entrada", "piso": 2, "ubicacion": "Pasillo principal piso 2", "ip_local": "192.168.1.51"},
    {"id": "term-p3-entrada", "descripcion": "Terminal Piso 3 Entrada", "piso": 3, "ubicacion": "Pasillo principal piso 3", "ip_local": "192.168.1.52"},
]

DEPARTAMENTOS = ["Tecnología", "Recursos Humanos", "Finanzas", "Marketing", "Operaciones"]

USUARIOS_PRUEBA = [
    {"nombre": "Ana",     "apellido": "García",   "email": "ana.garcia@empresa.com",   "departamento": "Tecnología",      "piso_preferido": 3},
    {"nombre": "Carlos",  "apellido": "López",    "email": "carlos.lopez@empresa.com",  "departamento": "Finanzas",        "piso_preferido": 2},
    {"nombre": "María",   "apellido": "Martínez", "email": "maria.martinez@empresa.com","departamento": "Recursos Humanos","piso_preferido": 1},
    {"nombre": "Pedro",   "apellido": "Sánchez",  "email": "pedro.sanchez@empresa.com", "departamento": "Marketing",       "piso_preferido": 2},
    {"nombre": "Lucía",   "apellido": "Fernández","email": "lucia.fernandez@empresa.com","departamento": "Tecnología",     "piso_preferido": 3},
    {"nombre": "Diego",   "apellido": "Torres",   "email": "diego.torres@empresa.com",  "departamento": "Operaciones",     "piso_preferido": 1},
]

async def seed():
    async with AsyncSessionLocal() as db:
        # Controladores
        for c in CONTROLADORES:
            await db.execute(
                text("""INSERT INTO controladores (id, descripcion, piso, zona, ip_local)
                   VALUES (:id, :descripcion, :piso, :zona, :ip_local)
                   ON CONFLICT (id) DO NOTHING"""),
                c
            )

        # Terminales
        for t in TERMINALES:
            await db.execute(
                text("""INSERT INTO terminales (id, descripcion, piso, ubicacion, ip_local)
                   VALUES (:id, :descripcion, :piso, :ubicacion, :ip_local)
                   ON CONFLICT (id) DO NOTHING"""),
                t
            )

        # Casilleros (25 por controlador = 125 total)
        casillero_num = 1
        for ctrl in CONTROLADORES:
            for puerto in range(1, 26):
                numero = f"{ctrl['zona']}{ctrl['piso']}-{casillero_num:03d}"
                await db.execute(
                    text("""INSERT INTO casilleros (numero, piso, zona, controlador_id, puerto_controlador)
                       VALUES (:numero, :piso, :zona, :controlador_id, :puerto)
                       ON CONFLICT (numero) DO NOTHING"""),
                    {
                        "numero": numero,
                        "piso": ctrl["piso"],
                        "zona": ctrl["zona"],
                        "controlador_id": ctrl["id"],
                        "puerto": (puerto % 8) + 1,
                    }
                )
                casillero_num += 1

        # Usuarios de prueba
        for u in USUARIOS_PRUEBA:
            await db.execute(
                text("""INSERT INTO usuarios (nombre, apellido, email, departamento, piso_preferido, estado)
                   VALUES (:nombre, :apellido, :email, :departamento, :piso_preferido, 'activo')
                   ON CONFLICT (email) DO NOTHING"""),
                u
            )

        await db.commit()
        print(f"✅ Seed completado:")
        print(f"   - {len(CONTROLADORES)} controladores")
        print(f"   - {len(TERMINALES)} terminales")
        print(f"   - {casillero_num - 1} casilleros")
        print(f"   - {len(USUARIOS_PRUEBA)} usuarios de prueba")

if __name__ == "__main__":
    asyncio.run(seed())
