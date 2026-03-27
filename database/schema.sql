-- ============================================================
--  SISTEMA DE CASILLEROS AUTOMATIZADOS
--  Esquema completo PostgreSQL
-- ============================================================

-- Extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUMS
-- ============================================================

CREATE TYPE estado_usuario AS ENUM (
    'pendiente_biometria',
    'activo',
    'inactivo'
);

CREATE TYPE estado_casillero AS ENUM (
    'libre',
    'ocupado',
    'bloqueado',
    'mantenimiento'
);

CREATE TYPE resultado_acceso AS ENUM (
    'exitoso',
    'denegado_biometria',
    'denegado_usuario_inactivo',
    'denegado_sin_casillero',
    'denegado_fuera_horario',
    'error_hardware'
);

CREATE TYPE rol_admin AS ENUM (
    'superadmin',
    'admin',
    'viewer'        -- Solo puede ver reportes, no modificar
);

-- ============================================================
-- TABLA: administradores
-- Usuarios que acceden al panel de gestión
-- ============================================================

CREATE TABLE administradores (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    apellido        VARCHAR(100) NOT NULL,
    email           VARCHAR(200) NOT NULL UNIQUE,
    password_hash   VARCHAR(500) NOT NULL,
    rol             rol_admin    NOT NULL DEFAULT 'admin',
    activo          BOOLEAN      NOT NULL DEFAULT TRUE,
    ultimo_acceso   TIMESTAMP,
    fecha_creacion  TIMESTAMP    NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP
);

-- ============================================================
-- TABLA: usuarios
-- Empleados que usan los casilleros
-- ============================================================

CREATE TABLE usuarios (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    apellido            VARCHAR(100) NOT NULL,
    email               VARCHAR(200) NOT NULL UNIQUE,
    departamento        VARCHAR(100) NOT NULL,
    piso_preferido      SMALLINT,
    estado              estado_usuario NOT NULL DEFAULT 'pendiente_biometria',
    fecha_creacion      TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP,
    creado_por_admin_id INTEGER REFERENCES administradores(id) ON DELETE SET NULL
);

-- ============================================================
-- TABLA: biometria
-- Vectores faciales encriptados. Uno por usuario.
-- NUNCA se guarda la foto, solo el vector matemático encriptado.
-- ============================================================

CREATE TABLE biometria (
    id                  SERIAL PRIMARY KEY,
    usuario_id          INTEGER NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    vector_encriptado   TEXT    NOT NULL,           -- AES-256 encriptado
    modelo_usado        VARCHAR(50) NOT NULL DEFAULT 'Facenet512',
    fecha_registro      TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP
);

-- ============================================================
-- TABLA: controladores
-- Dispositivos físicos que manejan las cerraduras (vía MQTT)
-- ============================================================

CREATE TABLE controladores (
    id              VARCHAR(100) PRIMARY KEY,       -- Ej: "ctrl-piso1-zona-a"
    descripcion     VARCHAR(200),
    piso            SMALLINT NOT NULL,
    zona            VARCHAR(50),
    ip_local        INET,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_ping     TIMESTAMP,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: casilleros
-- Cada casillero físico del sistema
-- ============================================================

CREATE TABLE casilleros (
    id                      SERIAL PRIMARY KEY,
    numero                  VARCHAR(20) NOT NULL UNIQUE,    -- Ej: "A-101"
    piso                    SMALLINT NOT NULL,
    zona                    VARCHAR(50) NOT NULL,
    controlador_id          VARCHAR(100) NOT NULL REFERENCES controladores(id),
    puerto_controlador      SMALLINT NOT NULL,              -- Puerto físico (1-8)
    estado                  estado_casillero NOT NULL DEFAULT 'libre',
    usuario_asignado_id     INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    fecha_asignacion        TIMESTAMP,
    observaciones           TEXT,

    -- Un controlador no puede tener dos casilleros en el mismo puerto
    CONSTRAINT uq_controlador_puerto UNIQUE (controlador_id, puerto_controlador)
);

-- ============================================================
-- TABLA: terminales
-- Dispositivos de reconocimiento facial (cámaras/pantallas)
-- ============================================================

CREATE TABLE terminales (
    id              VARCHAR(100) PRIMARY KEY,       -- Ej: "terminal-piso1-entrada"
    descripcion     VARCHAR(200),
    piso            SMALLINT NOT NULL,
    ubicacion       VARCHAR(200),
    ip_local        INET,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    ultimo_ping     TIMESTAMP,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- TABLA: accesos_log
-- Registro de CADA intento de acceso (exitoso o fallido)
-- Esta tabla crecerá mucho, está optimizada para escritura rápida
-- ============================================================

CREATE TABLE accesos_log (
    id                      BIGSERIAL PRIMARY KEY,  -- BIGSERIAL para volumen alto
    usuario_id              INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    casillero_id            INTEGER REFERENCES casilleros(id) ON DELETE SET NULL,
    terminal_id             VARCHAR(100),
    resultado               resultado_acceso NOT NULL,
    confianza_biometrica    NUMERIC(5,4),           -- Score 0.0000 - 1.0000
    timestamp               TIMESTAMP NOT NULL DEFAULT NOW(),
    detalle                 VARCHAR(500),
    ip_terminal             INET
);

-- ============================================================
-- TABLA: horarios_acceso
-- Define ventanas de tiempo permitidas por departamento
-- ============================================================

CREATE TABLE horarios_acceso (
    id              SERIAL PRIMARY KEY,
    departamento    VARCHAR(100),                   -- NULL = aplica a todos
    dia_semana      SMALLINT NOT NULL,              -- 0=Lunes ... 6=Domingo
    hora_inicio     TIME NOT NULL,
    hora_fin        TIME NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT chk_horario_valido CHECK (hora_inicio < hora_fin)
);

-- ============================================================
-- TABLA: alertas
-- Registro de eventos que requieren atención del administrador
-- ============================================================

CREATE TABLE alertas (
    id              BIGSERIAL PRIMARY KEY,
    tipo            VARCHAR(100) NOT NULL,          -- 'intentos_fallidos', 'hardware_offline', etc.
    descripcion     TEXT NOT NULL,
    terminal_id     VARCHAR(100),
    usuario_id      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    resuelta        BOOLEAN NOT NULL DEFAULT FALSE,
    resuelta_por    INTEGER REFERENCES administradores(id) ON DELETE SET NULL,
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_resolucion TIMESTAMP
);

-- ============================================================
-- ÍNDICES
-- Optimizados para las consultas más frecuentes del sistema
-- ============================================================

-- Accesos: consultas por usuario y por fecha (reportes)
CREATE INDEX idx_accesos_usuario_id     ON accesos_log(usuario_id);
CREATE INDEX idx_accesos_timestamp      ON accesos_log(timestamp DESC);
CREATE INDEX idx_accesos_terminal       ON accesos_log(terminal_id, timestamp DESC);
CREATE INDEX idx_accesos_resultado      ON accesos_log(resultado);

-- Casilleros: búsqueda de disponibles
CREATE INDEX idx_casilleros_estado      ON casilleros(estado);
CREATE INDEX idx_casilleros_piso        ON casilleros(piso, estado);
CREATE INDEX idx_casilleros_usuario     ON casilleros(usuario_asignado_id);

-- Usuarios: búsqueda por email y estado
CREATE INDEX idx_usuarios_email         ON usuarios(email);
CREATE INDEX idx_usuarios_estado        ON usuarios(estado);
CREATE INDEX idx_usuarios_departamento  ON usuarios(departamento);

-- Alertas: no resueltas primero
CREATE INDEX idx_alertas_resuelta       ON alertas(resuelta, fecha_creacion DESC);

-- ============================================================
-- VISTAS ÚTILES PARA EL PANEL
-- ============================================================

-- Vista: estado actual de cada casillero con datos del usuario asignado
CREATE VIEW v_casilleros_con_usuario AS
SELECT
    c.id,
    c.numero,
    c.piso,
    c.zona,
    c.estado,
    c.controlador_id,
    c.fecha_asignacion,
    u.id            AS usuario_id,
    u.nombre        AS usuario_nombre,
    u.apellido      AS usuario_apellido,
    u.email         AS usuario_email,
    u.departamento  AS usuario_departamento
FROM casilleros c
LEFT JOIN usuarios u ON c.usuario_asignado_id = u.id;

-- Vista: resumen de ocupación por piso
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
ORDER BY piso;

-- Vista: últimos accesos con nombre de usuario
CREATE VIEW v_accesos_recientes AS
SELECT
    al.id,
    al.timestamp,
    al.resultado,
    al.confianza_biometrica,
    al.terminal_id,
    al.detalle,
    u.nombre        AS usuario_nombre,
    u.apellido      AS usuario_apellido,
    u.departamento,
    c.numero        AS casillero_numero,
    c.piso          AS casillero_piso
FROM accesos_log al
LEFT JOIN usuarios u  ON al.usuario_id  = u.id
LEFT JOIN casilleros c ON al.casillero_id = c.id
ORDER BY al.timestamp DESC;

-- ============================================================
-- DATOS SEMILLA (horarios por defecto)
-- ============================================================

INSERT INTO horarios_acceso (departamento, dia_semana, hora_inicio, hora_fin) VALUES
-- Lunes a Viernes para todos los departamentos
(NULL, 0, '06:00', '22:00'),
(NULL, 1, '06:00', '22:00'),
(NULL, 2, '06:00', '22:00'),
(NULL, 3, '06:00', '22:00'),
(NULL, 4, '06:00', '22:00'),
-- Sábados horario reducido
(NULL, 5, '08:00', '14:00');
-- Domingos: sin acceso (no hay registro = no hay acceso)
