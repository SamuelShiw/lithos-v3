# db/repositories/estandares_repo.py
from db.supabase_client import get_supabase

def get_todos_estandares():
    response = get_supabase().table("estandares_config").select("*").eq("activo", True).execute()
    return response.data

def crear_estandar(nombre, ancho, alto, roca, densidad, malla, factor):
    try:
        data = {
            "nombre": nombre,
            "seccion_ancho": ancho,
            "seccion_alto": alto,
            "tipo_roca": roca,
            "densidad": densidad,
            "malla_taladros": malla,
            "factor_carga_tal": factor
        }
        get_supabase().table("estandares_config").insert(data).execute()
        return True, "Estándar de ingeniería creado."
    except Exception as e:
        return False, str(e)