#!/usr/bin/env python3
"""
scripts/backfill_model_snapshots.py
Backfill para crear estandar_versions (si no existen), enlazar labores y generar model_snapshots
Opciones:
  --days N       : procesar eventos de los últimos N días (default 90)
  --dry-run      : no escribe en BD, solo simula y muestra resumen
  --force        : regenerar snapshots si ya existen
"""
import argparse
import json
import hashlib
from datetime import datetime, timedelta

from db.supabase_client import get_supabase


def hash_snapshot(obj: dict) -> str:
    s = json.dumps(obj, sort_keys=True, default=str)
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def ensure_estandar_versions(client):
    # 1) Para cada estándar en estandares_config crear versión 1 si no existe
    res = client.table("estandares_config").select("*").execute()
    ests = res.data or []
    created = []
    for e in ests:
        # verificar si ya existe estandar_versions para este estandar
        q = client.table("estandar_versions").select("id").eq("estandar_id", e['id']).limit(1).execute()
        if q.data:
            continue
        # construir parametros (basado en columnas actuales)
        ancho = e.get('seccion_ancho') or 0
        alto = e.get('seccion_alto') or 0
        seccion_m2 = float(ancho) * float(alto)
        parametros = {
            "seccion_m2": seccion_m2,
            "densidad_t_m3": e.get('densidad'),
            "malla": {"type": "tal_por_tiro", "value": e.get('malla_taladros')},
            "metodo_explosivo": "kg_por_taladro",
            "kg_por_taladro": e.get('factor_carga_tal')
        }
        insert = {
            "estandar_id": e['id'],
            "version_number": 1,
            "parametros": parametros,
            "creado_por": "backfill_script",
            "notas": "Auto-backfill inicial"
        }
        client.table("estandar_versions").insert(insert).execute()
        created.append(e['id'])
    return created


def link_labores_to_version(client):
    # Asignar estandar_version_id a labores si estandar_id está presente
    labs = client.table("labores").select("*").execute().data or []
    updated = 0
    for l in labs:
        if l.get('estandar_version_id'):
            continue
        estandar_id = l.get('estandar_id')
        if not estandar_id:
            continue
        # obtener version más reciente (v=1 en backfill)
        ev = client.table("estandar_versions").select("id").eq("estandar_id", estandar_id).order("version_number", desc=True).limit(1).execute()
        if ev.data:
            ev_id = ev.data[0]['id']
            client.table("labores").update({"estandar_version_id": ev_id}).eq("id", l['id']).execute()
            updated += 1
    return updated


def fetch_events(client, days):
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    res = client.table("eventos_operativos").select("*").gte("created_at", since).execute()
    return res.data or []


def get_event_results(client, evento_id):
    res = client.table("resultados_fisicos").select("*").eq("evento_id", evento_id).execute()
    d = {"AVANCE_M":0.0, "TONELAJE":0.0, "TALADROS":0.0}
    for r in res.data or []:
        tipo = r.get('tipo_dato')
        if tipo in d:
            d[tipo] += float(r.get('cantidad_lograda', 0))
    return d


def backfill_events(client, events, dry_run=False, force=False):
    processed=0; skipped=0; created=0
    for e in events:
        eid = e['id']
        # skip if snapshot exists and not force
        q = client.table("model_snapshots").select("id").eq("evento_id", eid).limit(1).execute()
        if q.data and not force:
            skipped += 1
            continue

        # obtener labor y su estandar_version
        lab_id = e.get('labor_id')
        lab = client.table("labores").select("*").eq("id", lab_id).single().execute().data or {}
        ev_id = lab.get('estandar_version_id')
        if not ev_id:
            # intentar obtener por estandar_id en labores
            est_id = lab.get('estandar_id')
            if est_id:
                ev = client.table("estandar_versions").select("*").eq("estandar_id", est_id).order("version_number", desc=True).limit(1).execute()
                if ev.data:
                    ev_id = ev.data[0]['id']
        if not ev_id:
            # no podemos modelar sin estándar
            print(f"[WARN] evento {eid} sin estandar_version; se salta")
            skipped += 1
            continue

        ev_row = client.table("estandar_versions").select("*").eq("id", ev_id).single().execute().data
        parametros = ev_row.get('parametros') or {}

        # obtener resultados del evento
        res = get_event_results(client, eid)
        avance_m = float(res.get('AVANCE_M') or 0.0)
        ton_real = float(res.get('TONELAJE') or 0.0)
        tal_real = float(res.get('TALADROS') or 0.0)

        # calcular: volumen, ton_model, taladros_model, kg_model (basado en parametros simples)
        seccion_m2 = float(parametros.get('seccion_m2') or 0.0)
        dens = float(parametros.get('densidad_t_m3') or 0.0)
        malla = parametros.get('malla', {}).get('value') or None
        kg_por_tal = float(parametros.get('kg_por_taladro') or 0.0)

        volumen_m3 = seccion_m2 * avance_m
        ton_model = volumen_m3 * dens
        taladros_model = int(malla) if malla else 0
        kg_model = taladros_model * kg_por_tal

        inputs = {
            "avance_m": avance_m,
            "taladros_real": tal_real,
            "ton_real": ton_real,
            "seccion_m2": seccion_m2
        }
        steps = {
            "volumen_m3": volumen_m3,
            "taladros_model": taladros_model,
            "kg_model_calc": kg_model
        }
        outputs = {
            "volumen_m3": volumen_m3,
            "ton_model": ton_model,
            "kg_expl_model": kg_model,
            "taladros_model": taladros_model
        }

        snapshot = {
            "evento_id": eid,
            "creado_por": "backfill_script",
            "inputs": inputs,
            "parameters": parametros,
            "steps": steps,
            "outputs": outputs,
            "formula_id": "BACKFILL_V0",
            "checksum": hash_snapshot({"inputs":inputs, "parameters":parametros, "outputs":outputs})
        }

        if dry_run:
            print(f"[DRY] Evento {eid}: snapshot preview -> {json.dumps(snapshot, default=str)}")
            created += 1
            continue

        # Si existe y force==True, borrar antiguo y crear nuevo
        if q.data:
            old_id = q.data[0]['id']
            client.table("model_snapshots").delete().eq("id", old_id).execute()

        ins = client.table("model_snapshots").insert(snapshot).execute()
        new_snapshot_id = ins.data[0]['id'] if ins.data else None

        # actualizar evento con referencias y métricas rápidas
        delta_ton_pct = None
        if ton_model and ton_model != 0:
            delta_ton_pct = 100.0 * (ton_real - ton_model) / ton_model
        delta_kg_pct = None # kg_real not stored generally; can be calculated if consumos have data.

        upd = {
            "model_snapshot_id": new_snapshot_id,
            "estandar_version_id": ev_id,
            "ton_model": ton_model,
            "kg_expl_model": kg_model,
            "delta_ton_pct": delta_ton_pct
        }
        client.table("eventos_operativos").update(upd).eq("id", eid).execute()

        # insertar fila en model_deltas
        client.table("model_deltas").insert({
            "evento_id": eid,
            "ton_model": ton_model,
            "ton_real": ton_real,
            "delta_ton_pct": delta_ton_pct,
            "kg_model": kg_model,
            "kg_real": None,
            "delta_kg_pct": None
        }).execute()

        created += 1
        processed += 1

    return {"processed": processed, "skipped": skipped, "created": created}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    client = get_supabase()

    print("1) Asegurando versiones de estándares...")
    created = ensure_estandar_versions(client)
    print(f" - versiones creadas para estandares: {created}")

    print("2) Vinculando labores a versiones...")
    updated = link_labores_to_version(client)
    print(f" - labores actualizadas: {updated}")

    print(f"3) Obteniendo eventos de últimos {args.days} días...")
    events = fetch_events(client, args.days)
    print(f" - eventos a procesar: {len(events)}")

    summary = backfill_events(client, events, dry_run=args.dry_run, force=args.force)
    print("Resumen backfill:", summary)
    print("Hecho.")

if __name__ == "__main__":
    main()
