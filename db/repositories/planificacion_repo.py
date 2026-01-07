# mining_ops/db/repositories/planificacion_repo.py
from db.supabase_client import get_supabase

def get_presupuestos():
    client = get_supabase()
    try:
        # Traemos Labor y Actividad
        res = client.table("presupuestos").select(
            "*, labores(nombre), actividades_catalogo(nombre)"
        ).execute()
        return res.data
    except Exception:
        return []

def crear_presupuesto(labor_id, actividad_id, periodo, ton, mts, costo):
    client = get_supabase()
    data = {
        "labor_id": labor_id,
        "actividad_id": actividad_id, # NUEVO
        "periodo": periodo,
        "tonelaje_esp": ton,
        "metros_esp": mts,
        "costo_esp": costo
    }
    try:
        client.table("presupuestos").insert(data).execute()
        return True
    except Exception as e:
        print(e)
        return False

def get_dotacion():
    client = get_supabase()
    try:
        res = client.table("dotacion").select(
            "*, labores(nombre), actividades_catalogo(nombre)"
        ).execute()
        return res.data
    except Exception:
        return []

def crear_dotacion(labor_id, actividad_id, rol, cantidad):
    client = get_supabase()
    data = {
        "labor_id": labor_id, 
        "actividad_id": actividad_id, # NUEVO
        "rol": rol, 
        "cantidad": cantidad
    }
    try:
        client.table("dotacion").insert(data).execute()
        return True
    except Exception as e:
        print(e)
        return False