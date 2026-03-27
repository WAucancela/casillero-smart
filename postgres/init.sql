-- ══════════════════════════════════════════════════════════════
--  Inicialización de PostgreSQL
--  Se ejecuta solo la primera vez que se crea el contenedor.
--  Las tablas las crea Alembic (servicio "migrate").
-- ══════════════════════════════════════════════════════════════

-- Extensiones útiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- búsqueda de texto fuzzy

-- Zona horaria por defecto
ALTER DATABASE casilleros SET timezone TO 'America/Guayaquil';

-- Permisos del usuario de aplicación
GRANT ALL PRIVILEGES ON DATABASE casilleros TO casilleros_user;
GRANT ALL ON SCHEMA public TO casilleros_user;
