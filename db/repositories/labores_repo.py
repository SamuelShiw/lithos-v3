from db.supabase_client import get_supabase
from datetime import datetime
import re

# ==============================================================================
#  CONSULTAS (LECTURA)
# ==============================================================================

def get_todas_labores():
    """
    Uso: Módulo 4 (Configuración).
    Trae TODAS las labores (Activas, Paradas, Cerradas) para gestionarlas.
    """
    client = get_supabase()
    response = client.table("labores").select("*").order("nombre").execute()
    return response.data

def get_labores_activas():
    """
    Uso: Módulo 1 (Registro) y Módulo 2 (Consultas).
    Trae SOLO las labores que están operativas ('ACTIVA').
    Oculta las Paradas, Standby o Cerradas para no ensuciar el registro diario.
    """
    client = get_supabase()
    
    # Filtramos por la columna de ciclo de vida
    response = client.table("labores")\
        .select("*")\
        .eq("estado_ciclo", "ACTIVA")\
        .order("nombre")\
        .execute()
    
    return response.data

# ==============================================================================
#  TRANSACCIONES (ESCRITURA)
# ==============================================================================

def crear_labor(nombre, zona_nivel, tipo_geo, estandar_id): # <--- Nuevo parámetro
    try:
        data = {
            "nombre": nombre,
            "zona_nivel": zona_nivel,
            "tipo_geometrico": tipo_geo, # Ajustar según tu columna real o usar diccionario
            "estandar_id": estandar_id # <--- VINCULACIÓN
        }
        get_supabase().table("labores").insert(data).execute()
        return True, "Labor creada y vinculada al estándar."
    except Exception as e:
        return False, str(e)

def cambiar_estado_labor(labor_id, nuevo_estado, motivo):
    """
    Actualiza el ciclo de vida de la labor (Activa <-> Parada <-> Cerrada).
    """
    client = get_supabase()
    
    data = {
        "estado_ciclo": nuevo_estado,
        "motivo_estado": motivo,
        "fecha_estado": datetime.now().isoformat()
    }
    
    try:
        client.table("labores").update(data).eq("id", labor_id).execute()
        return True, f"Labor pasó a {nuevo_estado}"
    except Exception as e:
        return False, str(e)