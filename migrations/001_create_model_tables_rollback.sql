-- 001_create_model_tables_rollback.sql
BEGIN;

-- rollback seguro: eliminar vistas/materialized views dependientes antes de borrar tablas
-- Ejecutar manualmente la consulta para listar matviews que dependan de model_snapshots si se desea

-- 1) Eliminar vistas materializadas que dependen de model_snapshots
DROP MATERIALIZED VIEW IF EXISTS mv_eventos_kpis;

-- Añadir DROP de otras vistas dependientes si existen
-- DROP MATERIALIZED VIEW IF EXISTS otra_vista_relacionada;

-- 2) Revertir columnas añadidas
ALTER TABLE eventos_operativos
  DROP COLUMN IF EXISTS delta_kg_pct,
  DROP COLUMN IF EXISTS delta_ton_pct,
  DROP COLUMN IF EXISTS kg_expl_model,
  DROP COLUMN IF EXISTS ton_model,
  DROP COLUMN IF EXISTS model_snapshot_id,
  DROP COLUMN IF EXISTS estandar_version_id;

ALTER TABLE labores
  DROP COLUMN IF EXISTS estandar_version_id;

ALTER TABLE recursos_catalogo
  DROP COLUMN IF EXISTS codigo_producto,
  DROP COLUMN IF EXISTS metodo_medida,
  DROP COLUMN IF EXISTS peso_unitario_kg;

-- 3) Eliminar tablas nuevas (ahora sin dependencias)
DROP INDEX IF EXISTS idx_model_deltas_evento;
DROP TABLE IF EXISTS model_deltas;

DROP INDEX IF EXISTS idx_snapshot_evento;
DROP TABLE IF EXISTS model_snapshots;

DROP INDEX IF EXISTS idx_estandar_versions_estandar_fecha;
DROP TABLE IF EXISTS estandar_versions;

DROP INDEX IF EXISTS idx_audit_entidad;
DROP TABLE IF EXISTS audit_logs;

COMMIT;
