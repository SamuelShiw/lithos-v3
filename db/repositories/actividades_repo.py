from db.supabase_client import get_supabase

def get_actividades_activas(filtro_geo_id=None):
    """
    Uso: Módulo 1 (Registro). 
    Solo trae las activas para no ensuciar la lista del operador.
    """
    client = get_supabase()
    query = client.table("actividades_catalogo").select("*").eq("activo", True).order("nombre")
    
    # Filtro opcional por geometría (si tu BD lo usa)
    if filtro_geo_id:
        query = query.eq("tipo_geometrico_id", filtro_geo_id)
        
    response = query.execute()
    return response.data

def get_todas_actividades():
    """
    Uso: Módulo 4 (Configuración).
    Trae TODO el catálogo para gestión.
    """
    client = get_supabase()
    response = client.table("actividades_catalogo").select("*").order("nombre").execute()
    return response.data

def crear_actividad(nombre, unidad, req_ton, req_mts, req_tal):
    """
    Crea una nueva regla de negocio (Actividad).
    """
    client = get_supabase()
    data = {
        "nombre": nombre,
        "unidad_produccion": unidad,
        "req_tonelaje": req_ton,
        "req_avance": req_mts,
        "req_taladros": req_tal,
        "activo": True
    }
    try:
        client.table("actividades_catalogo").insert(data).execute()
        return True, "Actividad creada correctamente."
    except Exception as e:
        return False, str(e)

def toggle_actividad(id_actividad, estado_actual):
    """
    Activa o Desactiva una actividad (Soft Delete).
    """
    client = get_supabase()
    try:
        client.table("actividades_catalogo").update({"activo": not estado_actual}).eq("id", id_actividad).execute()
        return True, "Estado actualizado."
    except Exception as e:
        return False, str(e)