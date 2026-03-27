"""001 - tablas base del sistema

Revision ID: 001_tablas_base
Revises:
Create Date: 2026-03-11
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_tablas_base'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Enums
    estado_usuario = postgresql.ENUM(
        'pendiente_biometria', 'activo', 'inactivo',
        name='estado_usuario'
    )
    estado_casillero = postgresql.ENUM(
        'libre', 'ocupado', 'bloqueado', 'mantenimiento',
        name='estado_casillero'
    )
    resultado_acceso = postgresql.ENUM(
        'exitoso', 'denegado_biometria', 'denegado_usuario_inactivo',
        'denegado_sin_casillero', 'denegado_fuera_horario', 'error_hardware',
        name='resultado_acceso'
    )
    rol_admin = postgresql.ENUM(
        'superadmin', 'admin', 'viewer',
        name='rol_admin'
    )
    estado_usuario.create(op.get_bind(),checkfirst=True)
    estado_casillero.create(op.get_bind(),checkfirst=True)
    resultado_acceso.create(op.get_bind(),checkfirst=True)
    rol_admin.create(op.get_bind(),checkfirst=True)

    # administradores
    op.create_table('administradores',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100), nullable=False),
        sa.Column('email', sa.String(200), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(500), nullable=False),
        sa.Column('rol', sa.Enum('superadmin', 'admin', 'viewer', name='rol_admin'), nullable=False, server_default='admin'),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ultimo_acceso', sa.DateTime),
        sa.Column('fecha_creacion', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('fecha_actualizacion', sa.DateTime),
    )

    # usuarios
    op.create_table('usuarios',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('nombre', sa.String(100), nullable=False),
        sa.Column('apellido', sa.String(100), nullable=False),
        sa.Column('email', sa.String(200), nullable=False, unique=True),
        sa.Column('departamento', sa.String(100), nullable=False),
        sa.Column('piso_preferido', sa.SmallInteger),
        sa.Column('estado', sa.Enum('pendiente_biometria', 'activo', 'inactivo', name='estado_usuario'), nullable=False, server_default='pendiente_biometria'),
        sa.Column('fecha_creacion', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('fecha_actualizacion', sa.DateTime),
        sa.Column('creado_por_admin_id', sa.Integer, sa.ForeignKey('administradores.id', ondelete='SET NULL')),
    )

    # biometria
    op.create_table('biometria',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('vector_encriptado', sa.Text, nullable=False),
        sa.Column('modelo_usado', sa.String(50), nullable=False, server_default='Facenet512'),
        sa.Column('fecha_registro', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('fecha_actualizacion', sa.DateTime),
    )

    # controladores
    op.create_table('controladores',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('descripcion', sa.String(200)),
        sa.Column('piso', sa.SmallInteger, nullable=False),
        sa.Column('zona', sa.String(50)),
        sa.Column('ip_local', postgresql.INET),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ultimo_ping', sa.DateTime),
        sa.Column('fecha_creacion', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )

    # casilleros
    op.create_table('casilleros',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('numero', sa.String(20), nullable=False, unique=True),
        sa.Column('piso', sa.SmallInteger, nullable=False),
        sa.Column('zona', sa.String(50), nullable=False),
        sa.Column('controlador_id', sa.String(100), sa.ForeignKey('controladores.id'), nullable=False),
        sa.Column('puerto_controlador', sa.SmallInteger, nullable=False),
        sa.Column('estado', sa.Enum('libre', 'ocupado', 'bloqueado', 'mantenimiento', name='estado_casillero'), nullable=False, server_default='libre'),
        sa.Column('usuario_asignado_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('fecha_asignacion', sa.DateTime),
        sa.Column('observaciones', sa.Text),
        sa.UniqueConstraint('controlador_id', 'puerto_controlador', name='uq_controlador_puerto'),
    )

    # terminales
    op.create_table('terminales',
        sa.Column('id', sa.String(100), primary_key=True),
        sa.Column('descripcion', sa.String(200)),
        sa.Column('piso', sa.SmallInteger, nullable=False),
        sa.Column('ubicacion', sa.String(200)),
        sa.Column('ip_local', postgresql.INET),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
        sa.Column('ultimo_ping', sa.DateTime),
        sa.Column('fecha_creacion', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
    )

    # accesos_log
    op.create_table('accesos_log',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('casillero_id', sa.Integer, sa.ForeignKey('casilleros.id', ondelete='SET NULL')),
        sa.Column('terminal_id', sa.String(100)),
        sa.Column('resultado', sa.Enum(
            'exitoso', 'denegado_biometria', 'denegado_usuario_inactivo',
            'denegado_sin_casillero', 'denegado_fuera_horario', 'error_hardware',
            name='resultado_acceso'), nullable=False),
        sa.Column('confianza_biometrica', sa.Numeric(5, 4)),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('detalle', sa.String(500)),
        sa.Column('ip_terminal', postgresql.INET),
    )

    # horarios_acceso
    op.create_table('horarios_acceso',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('departamento', sa.String(100)),
        sa.Column('dia_semana', sa.SmallInteger, nullable=False),
        sa.Column('hora_inicio', sa.Time, nullable=False),
        sa.Column('hora_fin', sa.Time, nullable=False),
        sa.Column('activo', sa.Boolean, nullable=False, server_default='true'),
    )

    # alertas
    op.create_table('alertas',
        sa.Column('id', sa.BigInteger, primary_key=True),
        sa.Column('tipo', sa.String(100), nullable=False),
        sa.Column('descripcion', sa.Text, nullable=False),
        sa.Column('terminal_id', sa.String(100)),
        sa.Column('usuario_id', sa.Integer, sa.ForeignKey('usuarios.id', ondelete='SET NULL')),
        sa.Column('resuelta', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('resuelta_por', sa.Integer, sa.ForeignKey('administradores.id', ondelete='SET NULL')),
        sa.Column('fecha_creacion', sa.DateTime, nullable=False, server_default=sa.text('NOW()')),
        sa.Column('fecha_resolucion', sa.DateTime),
    )

    # Índices
    op.create_index('idx_accesos_usuario_id',  'accesos_log', ['usuario_id'])
    op.create_index('idx_accesos_timestamp',   'accesos_log', [sa.text('timestamp DESC')])
    op.create_index('idx_accesos_resultado',   'accesos_log', ['resultado'])
    op.create_index('idx_casilleros_estado',   'casilleros',  ['estado'])
    op.create_index('idx_casilleros_piso',     'casilleros',  ['piso', 'estado'])
    op.create_index('idx_casilleros_usuario',  'casilleros',  ['usuario_asignado_id'])
    op.create_index('idx_usuarios_email',      'usuarios',    ['email'])
    op.create_index('idx_usuarios_estado',     'usuarios',    ['estado'])
    op.create_index('idx_usuarios_depto',      'usuarios',    ['departamento'])
    op.create_index('idx_alertas_resuelta',    'alertas',     [sa.text('resuelta, fecha_creacion DESC')])

def downgrade() -> None:
    op.drop_table('alertas')
    op.drop_table('horarios_acceso')
    op.drop_table('accesos_log')
    op.drop_table('terminales')
    op.drop_table('casilleros')
    op.drop_table('controladores')
    op.drop_table('biometria')
    op.drop_table('usuarios')
    op.drop_table('administradores')
    for enum in ['estado_usuario', 'estado_casillero', 'resultado_acceso', 'rol_admin']:
        op.execute(f'DROP TYPE IF EXISTS {enum}')
