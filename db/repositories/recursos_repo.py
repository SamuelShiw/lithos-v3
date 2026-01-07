from db.supabase_client import get_supabase

def get_recursos_activos():
    """
    Uso: Módulo 1 (Registro).
    """
    client = get_supabase()
    # Trae diccionarios con las claves: 'unidad_medida', 'costo_unitario', etc.
    response = client.table("recursos_catalogo").select("*").eq("activo", True).order("tipo").execute()
    return response.data

def get_todos_recursos():
    """
    Uso: Módulo 4 (Configuración).
    """
    client = get_supabase()
    response = client.table("recursos_catalogo").select("*").order("tipo").execute()
    return response.data

def crear_recurso(nombre, unidad, tipo, costo):
    """
    Crea recurso usando los nombres de columna REALES de la BD.
    """
    client = get_supabase()
    data = {
        "nombre": nombre,
        "unidad_medida": unidad,    # <--- CORREGIDO (Era 'unidad')
        "tipo": tipo,
        "costo_unitario": costo,    # <--- CORREGIDO (Era 'costo_actual')
        "activo": True
    }
    try:
        client.table("recursos_catalogo").insert(data).execute()
        return True, "Recurso creado exitosamente."
    except Exception as e:
        return False, str(e)

def actualizar_precio_recurso(id_recurso, nuevo_precio):
    """
    Actualiza el precio unitario.
    """
    client = get_supabase()
    try:
        # <--- CORREGIDO 'costo_unitario'
        client.table("recursos_catalogo").update({"costo_unitario": nuevo_precio}).eq("id", id_recurso).execute()
        return True, "Precio actualizado."
    except Exception as e:
        return False, str(e)

def toggle_recurso(id_recurso, estado_actual):
    client = get_supabase()
    try:
        client.table("recursos_catalogo").update({"activo": not estado_actual}).eq("id", id_recurso).execute()
        return True, "Estado actualizado."
    except Exception as e:
        return False, str(e)