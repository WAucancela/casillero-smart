"""002 - vistas y datos semilla

Revision ID: 002_vistas_seeds
Revises: 001_tablas_base
Create Date: 2026-03-11
"""
from alembic import op
from passlib.context import CryptContext

revision = '002_vistas_seeds'
down_revision = '001_tablas_base'
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def upgrade() -> None:
    # Vista: casilleros con datos del usuario asignado
    op.execute("""
        CREATE VIEW v_casilleros_con_usuario AS
        SELECT
            c.id, c.numero, c.piso, c.zona, c.estado,
            c.controlador_id, c.fecha_asignacion,
            u.id            AS usuario_id,
            u.nombre        AS usuario_nombre,
            u.apellido      AS usuario_apellido,
            u.email         AS usuario_email,
            u.departamento  AS usuario_departamento
        FROM casilleros c
        LEFT JOIN usuarios u ON c.usuario_asignado_id = u.id
    """)

    # Vista: ocupación por piso
    op.execute("""
        CREATE VIEW v_ocupacion_por_piso AS
        SELECT
            piso,
            COUNT(*)                                        AS total,
            COUNT(*) FILTER (WHERE estado = 'ocupado')      AS ocupados,
            COUNT(*) FILTER (WHERE estado = 'libre')        AS libres,
            COUNT(*) FILTER (WHERE estado = 'bloqueado')    AS bloqueados,
            ROUND(
                COUNT(*) FILTER (WHERE estado = 'ocupado')::NUMERIC
                / NULLIF(COUNT(*), 0) * 100, 2
            )                                               AS porcentaje_ocupacion
        FROM casilleros
        GROUP BY piso
        ORDER BY piso
    """)

    # Vista: accesos recientes con nombres
    op.execute("""
        CREATE VIEW v_accesos_recientes AS
        SELECT
            al.id, al.timestamp, al.resultado,
            al.confianza_biometrica, al.terminal_id, al.detalle,
            u.nombre        AS usuario_nombre,
            u.apellido      AS usuario_apellido,
            u.departamento,
            c.numero        AS casillero_numero,
            c.piso          AS casillero_piso
        FROM accesos_log al
        LEFT JOIN usuarios u   ON al.usuario_id   = u.id
        LEFT JOIN casilleros c ON al.casillero_id = c.id
        ORDER BY al.timestamp DESC
    """)

    # Horarios por defecto (Lunes-Viernes + Sábado reducido)
    op.execute("""
        INSERT INTO horarios_acceso (departamento, dia_semana, hora_inicio, hora_fin) VALUES
        (NULL, 0, '06:00', '22:00'),
        (NULL, 1, '06:00', '22:00'),
        (NULL, 2, '06:00', '22:00'),
        (NULL, 3, '06:00', '22:00'),
        (NULL, 4, '06:00', '22:00'),
        (NULL, 5, '08:00', '14:00')
    """)

    # Administrador superadmin por defecto
    # ⚠️ CAMBIAR CONTRASEÑA ANTES DE PRODUCCIÓN
    password_hash = pwd_context.hash("Admin123!")
    op.execute(
        "INSERT INTO administradores (nombre, apellido, email, password_hash, rol) "
        "VALUES ('Super', 'Admin', 'admin@empresa.com', :hash, 'superadmin')",
        {"hash": password_hash},
    )

    # Controladores de cerraduras (uno por piso)
    op.execute("""
        INSERT INTO controladores (id, descripcion, piso, zona, ip_local, activo) VALUES
        ('CTRL-P1', 'Controlador Piso 1', 1, 'Zona A', '192.168.1.10', true),
        ('CTRL-P2', 'Controlador Piso 2', 2, 'Zona B', '192.168.1.11', true),
        ('CTRL-P3', 'Controlador Piso 3', 3, 'Zona C', '192.168.1.12', true)
    """)

    # Casilleros iniciales (15 en 3 pisos)
    op.execute("""
        INSERT INTO casilleros (numero, piso, zona, controlador_id, puerto_controlador, estado) VALUES
        ('A-101', 1, 'Zona A', 'CTRL-P1', 1, 'libre'),
        ('A-102', 1, 'Zona A', 'CTRL-P1', 2, 'libre'),
        ('A-103', 1, 'Zona A', 'CTRL-P1', 3, 'libre'),
        ('A-104', 1, 'Zona A', 'CTRL-P1', 4, 'libre'),
        ('A-105', 1, 'Zona A', 'CTRL-P1', 5, 'libre'),
        ('B-201', 2, 'Zona B', 'CTRL-P2', 1, 'libre'),
        ('B-202', 2, 'Zona B', 'CTRL-P2', 2, 'libre'),
        ('B-203', 2, 'Zona B', 'CTRL-P2', 3, 'libre'),
        ('B-204', 2, 'Zona B', 'CTRL-P2', 4, 'libre'),
        ('B-205', 2, 'Zona B', 'CTRL-P2', 5, 'libre'),
        ('C-301', 3, 'Zona C', 'CTRL-P3', 1, 'libre'),
        ('C-302', 3, 'Zona C', 'CTRL-P3', 2, 'libre'),
        ('C-303', 3, 'Zona C', 'CTRL-P3', 3, 'libre'),
        ('C-304', 3, 'Zona C', 'CTRL-P3', 4, 'libre'),
        ('C-305', 3, 'Zona C', 'CTRL-P3', 5, 'libre')
    """)

def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_accesos_recientes")
    op.execute("DROP VIEW IF EXISTS v_ocupacion_por_piso")
    op.execute("DROP VIEW IF EXISTS v_casilleros_con_usuario")
    op.execute("DELETE FROM horarios_acceso")
    op.execute("DELETE FROM administradores WHERE email = 'admin@empresa.com'")
    op.execute("DELETE FROM casilleros")
    op.execute("DELETE FROM controladores")
