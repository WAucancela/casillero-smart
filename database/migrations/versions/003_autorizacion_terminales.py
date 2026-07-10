"""003 - autorización de terminales ZKTeco

Antes de esta migración, cualquier dispositivo que conociera la URL del
webhook ADMS (POST /iclock/cdata) podía enviar eventos de acceso para
cualquier PIN, sin que el backend verificara de ningún modo que el evento
viniera de un terminal ZKTeco legítimo ya registrado.

Esta migración agrega una columna `autorizado` a `terminales_zkteco`
(tabla creada hasta ahora solo vía Base.metadata.create_all, por eso el
CREATE TABLE IF NOT EXISTS) y un nuevo valor de resultado de acceso para
poder loguear los intentos de dispositivos no autorizados.

Revision ID: 003_autorizacion_terminales
Revises: 002_vistas_seeds
Create Date: 2026-07-06
"""
from alembic import op
import sqlalchemy as sa

revision = '003_autorizacion_terminales'
down_revision = '002_vistas_seeds'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE resultado_acceso ADD VALUE IF NOT EXISTS 'denegado_dispositivo_no_autorizado'")

    op.execute("""
        CREATE TABLE IF NOT EXISTS terminales_zkteco (
            id              SERIAL PRIMARY KEY,
            sn              VARCHAR(100) UNIQUE NOT NULL,
            ip              VARCHAR(50),
            descripcion     VARCHAR(200),
            piso            INTEGER DEFAULT 1,
            activo          BOOLEAN DEFAULT TRUE,
            ultimo_contacto TIMESTAMP,
            ultimo_evento   TIMESTAMP
        )
    """)
    op.execute("ALTER TABLE terminales_zkteco ADD COLUMN IF NOT EXISTS autorizado BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("CREATE INDEX IF NOT EXISTS idx_terminales_zkteco_sn ON terminales_zkteco (sn)")


def downgrade() -> None:
    op.execute("ALTER TABLE terminales_zkteco DROP COLUMN IF EXISTS autorizado")
    # Postgres no permite quitar un valor de un ENUM sin recrear el tipo;
    # se deja el valor 'denegado_dispositivo_no_autorizado' en su lugar.
