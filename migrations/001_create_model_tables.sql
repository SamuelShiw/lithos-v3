-- 001_create_model_tables.sql
-- Migration: create model snapshot tables and add necessary columns
BEGIN;

-- 1) estandar_versions (versionado de estándares)
CREATE TABLE IF NOT EXISTS estandar_versions (
  id              SERIAL PRIMARY KEY,
  estandar_id     INTEGER NOT NULL REFERENCES estandares_config(id) ON DELETE CASCADE,
  version_number  INTEGER NOT NULL DEFAULT 1,
  fecha_inicio    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  fecha_fin       TIMESTAMP WITH TIME ZONE,
  parametros      JSONB NOT NULL,
  notas           TEXT,
  creado_por      TEXT,
  created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  UNIQUE (estandar_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_estandar_versions_estandar_fecha ON estandar_versions(estandar_id, fecha_inicio);

-- 2) model_snapshots (traza inmutable del cálculo por evento)
CREATE TABLE IF NOT EXISTS model_snapshots (
  id               SERIAL PRIMARY KEY,
  evento_id        INTEGER REFERENCES eventos_operativos(id) ON DELETE SET NULL,
  creado_por       TEXT,
  fecha_creacion   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  inputs           JSONB NOT NULL,
  parameters       JSONB NOT NULL,
  steps            JSONB NOT NULL,
  outputs          JSONB NOT NULL,
  formula_id       TEXT,
  checksum         TEXT,
  created_at       TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_snapshot_evento ON model_snapshots(evento_id);

-- 3) model_deltas (resumen comparativo para consultas rápidas)
CREATE TABLE IF NOT EXISTS model_deltas (
  id           SERIAL PRIMARY KEY,
  evento_id    INTEGER NOT NULL REFERENCES eventos_operativos(id) ON DELETE CASCADE,
  ton_model    FLOAT,
  ton_real     FLOAT,
  delta_ton_pct FLOAT,
  kg_model     FLOAT,
  kg_real      FLOAT,
  delta_kg_pct FLOAT,
  created_at   TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_model_deltas_evento ON model_deltas(evento_id);

-- 4) audit_logs (registro de cambios críticos)
CREATE TABLE IF NOT EXISTS audit_logs (
  id         SERIAL PRIMARY KEY,
  entidad    TEXT NOT NULL,
  entidad_id INTEGER,
  accion     TEXT NOT NULL,
  usuario    TEXT,
  detalle    JSONB,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_entidad ON audit_logs(entidad, entidad_id);

-- 5) Alter tablas existentes: labores (vincular versión estándar)
ALTER TABLE labores
  ADD COLUMN IF NOT EXISTS estandar_version_id INTEGER REFERENCES estandar_versions(id);

-- 6) Alter eventos_operativos (guardar referencia y métricas)
ALTER TABLE eventos_operativos
  ADD COLUMN IF NOT EXISTS estandar_version_id INTEGER REFERENCES estandar_versions(id),
  ADD COLUMN IF NOT EXISTS model_snapshot_id INTEGER REFERENCES model_snapshots(id),
  ADD COLUMN IF NOT EXISTS ton_model FLOAT,
  ADD COLUMN IF NOT EXISTS kg_expl_model FLOAT,
  ADD COLUMN IF NOT EXISTS delta_ton_pct FLOAT,
  ADD COLUMN IF NOT EXISTS delta_kg_pct FLOAT;

-- 7) Recursos: parámetros físicos
ALTER TABLE recursos_catalogo
  ADD COLUMN IF NOT EXISTS peso_unitario_kg FLOAT,
  ADD COLUMN IF NOT EXISTS metodo_medida TEXT,
  ADD COLUMN IF NOT EXISTS codigo_producto TEXT;

COMMIT;
