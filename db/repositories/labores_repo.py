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

def crear_labor(nombre, tipo_geo_id, zona_nivel_texto):
    """
    Crea una labor nueva.
    Genera código automático y asigna estado inicial ACTIVA.
    """
    client = get_supabase()
    
    # Generar Código Automático (ej: "Tajo 340" -> "TAJO-340")
    codigo_clean = re.sub(r'[^a-zA-Z0-9]', '-', nombre.upper())
    codigo_final = codigo_clean[:20]

    data = {
        "nombre": nombre,
        "codigo": codigo_final,
        "zona_nivel": zona_nivel_texto, 
        "tipo_geometrico_id": tipo_geo_id,
        "estado_ciclo": "ACTIVA",
        "motivo_estado": "Creación Inicial",
        "fecha_estado": datetime.now().isoformat()
    }
    
    try:
        client.table("labores").insert(data).execute()
        return True, "Labor creada exitosamente."
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