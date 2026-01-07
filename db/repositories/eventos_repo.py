# mining_ops/db/repositories/eventos_repo.py
from db.supabase_client import get_supabase
from domain.models import EventoOperativo

def get_reporte_eventos(fecha_inicio, fecha_fin, labor_id=None):
    """
    Trae eventos con TODO el detalle anidado para el Módulo 2.
    Join profundo: Evento -> Consumos -> Recurso
    """
    client = get_supabase()
    
    # Construimos la query base
    query = client.table("eventos_operativos").select(
        """
        *,
        labores(nombre, nombre_geometrico),
        actividades_catalogo(nombre, unidad_produccion),
        responsable_registro,
        consumo_recursos(
            cantidad,
            precio_snapshot,
            recursos_catalogo(nombre, unidad, tipo)
        ),
        resultados_fisicos(tipo_dato, cantidad_lograda)
        """
    ).gte("fecha", fecha_inicio).lte("fecha", fecha_fin)
    
    # Filtro opcional por labor
    if labor_id:
        query = query.eq("labor_id", labor_id)
        
    # Ordenar por fecha y guardia (descendente)
    query = query.order("fecha", desc=True)
    
    try:
        response = query.execute()
        return response.data
    except Exception as e:
        print(f"Error fetching reporte: {e}")
        return []

def guardar_evento_atomico(data_evento, lista_consumos, lista_resultados):
    """
    Guarda el evento completo en una transacción.
    data_evento debe incluir: 
    fecha, guardia, labor_id, actividad_id, responsable_id, observaciones,
    estado_operativo, tiempo_improductivo, motivo_parada
    """
    client = get_supabase()
    
    # 1. Insertar Cabecera (Evento)
    res_ev = client.table("eventos_operativos").insert(data_evento).execute()
    if not res_ev.data:
        return False, "Error al crear cabecera del evento"
    
    evento_id = res_ev.data[0]['id']
    
    # ... (El resto de la lógica de consumos y resultados SE MANTIENE IGUAL) ...
    # Solo asegúrate de NO tocar la lógica de inserción de hijos.
    
    # Código existente de inserción de consumos...
    if lista_consumos:
        consumos_db = []
        for c in lista_consumos:
            consumos_db.append({
                "evento_id": evento_id,
                "recurso_id": c['id'],
                "cantidad": c['cantidad'],
                "precio_snapshot": c['precio']
            })
        client.table("consumo_recursos").insert(consumos_db).execute()

    # Código existente de inserción de resultados...
    if lista_resultados:
        resultados_db = []
        for r in lista_resultados:
            resultados_db.append({
                "evento_id": evento_id,
                "tipo_dato": r['tipo'],
                "cantidad_lograda": r['cantidad']
            })
        client.table("resultados_fisicos").insert(resultados_db).execute()
        
    return True, "Evento registrado correctamente"

# --- Funciones de Lectura (Módulo 2) ---

def listar_eventos_resumen(fecha_inicio=None, fecha_fin=None, labor_id=None):
    client = get_supabase()
    query = client.table("eventos_operativos").select(
        "id, fecha, guardia, responsable_registro, observaciones, labores(nombre), actividades_catalogo(nombre)"
    )
    
    if fecha_inicio:
        query = query.gte("fecha", fecha_inicio)
    if fecha_fin:
        query = query.lte("fecha", fecha_fin)
    if labor_id:
        query = query.eq("labor_id", labor_id)
        
    res = query.order("fecha", desc=True).execute()
    return res.data

def obtener_detalle_evento(evento_id: int):
    client = get_supabase()
    
    # 1. Cabecera
    cabecera = client.table("eventos_operativos").select(
        "*, labores(nombre, zona_nivel), actividades_catalogo(nombre)"
    ).eq("id", evento_id).single().execute()
    
    # 2. Consumos
    consumos = client.table("consumo_recursos").select(
        "cantidad, precio_snapshot, recursos_catalogo(nombre, unidad_medida)"
    ).eq("evento_id", evento_id).execute()
    
    # 3. Resultados
    resultados = client.table("resultados_fisicos").select(
        "tipo_dato, cantidad_lograda"
    ).eq("evento_id", evento_id).execute()
    
    return {
        "evento": cabecera.data,
        "consumos": consumos.data,
        "resultados": resultados.data
    }
# mining_ops/db/repositories/eventos_repo.py

# ... (mantén imports y guardar_evento_atomico)

def listar_eventos_resumen(fecha_inicio=None, fecha_fin=None, labor_id=None, guardia=None):
    """
    Módulo 2: Listado inteligente. 
    Trae cabecera + resultados físicos aplanados para mostrar en la tabla resumen.
    """
    client = get_supabase()
    
    # Seleccionamos cabecera Y resultados físicos anidados
    query = client.table("eventos_operativos").select(
        "id, fecha, guardia, responsable_registro, observaciones, created_at, "
        "labores(nombre), actividades_catalogo(nombre), "
        "resultados_fisicos(tipo_dato, cantidad_lograda)"
    )
    
    if fecha_inicio: query = query.gte("fecha", fecha_inicio)
    if fecha_fin: query = query.lte("fecha", fecha_fin)
    if labor_id: query = query.eq("labor_id", labor_id)
    if guardia: query = query.eq("guardia", guardia)
        
    res = query.order("fecha", desc=True).execute()
    data = res.data
    
    # Procesamiento en Python para "Aplanar" la respuesta
    # Queremos que Tonelaje y Avance sean columnas, no filas anidadas
    lista_plana = []
    for e in data:
        # Extraer métricas clave
        ton = 0
        mts = 0
        for r in e.get('resultados_fisicos', []):
            if r['tipo_dato'] == 'TONELAJE': ton += r['cantidad_lograda']
            elif r['tipo_dato'] == 'AVANCE_M': mts += r['cantidad_lograda']
            
        fila = {
            "id": e['id'],
            "fecha": e['fecha'],
            "guardia": e['guardia'],
            "labor": e['labores']['nombre'] if e['labores'] else "---",
            "actividad": e['actividades_catalogo']['nombre'] if e['actividades_catalogo'] else "---",
            "responsable": e['responsable_registro'],
            "tonelaje": ton,
            "avance": mts,
            "estado": "Validado", # Por ahora hardcodeado, luego vendrá de BD
            "created_at": e['created_at']
        }
        lista_plana.append(fila)
        
    return lista_plana

# ... (mantén obtener_detalle_evento igual)
# mining_ops/db/repositories/eventos_repo.py
from db.supabase_client import get_supabase

# ... (mantén guardar_evento_atomico y obtener_detalle_evento igual) ...

def listar_eventos_resumen(fecha_inicio, fecha_fin, labor_id=None, guardia=None):
    """
    Trae la lista de eventos y 'aplana' los resultados físicos (Ton, Avance)
    para mostrarlos en la tabla resumen del Módulo 2.
    """
    client = get_supabase()
    
    # Query base
    query = client.table("eventos_operativos").select(
        "id, fecha, guardia, responsable_registro, observaciones, created_at, "
        "labores(nombre), actividades_catalogo(nombre), "
        "resultados_fisicos(tipo_dato, cantidad_lograda)" # Traemos los hijos anidados
    )
    
    # Filtros de Base de Datos
    query = query.gte("fecha", fecha_inicio).lte("fecha", fecha_fin)
    if labor_id:
        query = query.eq("labor_id", labor_id)
    if guardia:
        query = query.eq("guardia", guardia)
        
    res = query.order("fecha", desc=True).execute()
    data = res.data
    
    # Procesamiento (Aplanado)
    lista_plana = []
    for e in data:
        # Extraer métricas clave de la lista anidada
        ton = 0
        mts = 0
        tal = 0
        
        # Recorremos los resultados físicos de este evento
        for r in e.get('resultados_fisicos', []):
            if r['tipo_dato'] == 'TONELAJE': ton = r['cantidad_lograda']
            elif r['tipo_dato'] == 'AVANCE_M': mts = r['cantidad_lograda']
            elif r['tipo_dato'] == 'TALADROS': tal = r['cantidad_lograda']
            
        fila = {
            "id": e['id'],
            "fecha": e['fecha'],
            "guardia": e['guardia'],
            "labor": e['labores']['nombre'] if e['labores'] else "---",
            "actividad": e['actividades_catalogo']['nombre'] if e['actividades_catalogo'] else "---",
            "responsable": e['responsable_registro'],
            "tonelaje": ton,
            "avance": mts,
            "taladros": tal,
            "estado": "Validado", # Placeholder por ahora
            "created_at": e['created_at']
        }
        lista_plana.append(fila)
        
    return lista_plana

def guardar_evento_atomico(data_evento, lista_consumos, lista_resultados):
    """
    Guarda el evento completo en una transacción (Cabecera + Hijos).
    """
    client = get_supabase()
    
    # 1. Insertar Cabecera
    try:
        res_ev = client.table("eventos_operativos").insert(data_evento).execute()
        if not res_ev.data:
            return False, "No se pudo crear el evento (BD retornó vacío)."
        
        evento_id = res_ev.data[0]['id']
        
        # 2. Insertar Consumos
        if lista_consumos:
            consumos_db = []
            for c in lista_consumos:
                consumos_db.append({
                    "evento_id": evento_id,
                    "recurso_id": c['id'],
                    "cantidad": c['cantidad'],
                    "precio_snapshot": c['precio']
                })
            client.table("consumo_recursos").insert(consumos_db).execute()

        # 3. Insertar Resultados
        if lista_resultados:
            resultados_db = []
            for r in lista_resultados:
                resultados_db.append({
                    "evento_id": evento_id,
                    "tipo_dato": r['tipo'],
                    "cantidad_lograda": r['cantidad']
                })
            client.table("resultados_fisicos").insert(resultados_db).execute()
            
        return True, "Evento registrado correctamente"
        
    except Exception as e:
        print(f"CRITICAL ERROR al guardar: {e}")
        return False, str(e)

def get_reporte_eventos(fecha_inicio, fecha_fin, labor_id=None):
    """
    Trae el reporte con joins.
    Ajusta la fecha fin para incluir todo el día hasta las 23:59:59.
    """
    client = get_supabase()
    
    # AJUSTE DE FECHAS: Asegurar formato completo
    # Si fecha_fin es '2026-01-04', le agregamos hora final para que tome todo el día
    f_inicio_full = f"{fecha_inicio}T00:00:00"
    f_fin_full = f"{fecha_fin}T23:59:59"
    
    print(f"🔍 Consultando eventos entre {f_inicio_full} y {f_fin_full}...")

    # Query con Joins Explícitos
    # Nota: Supabase requiere que las relaciones existan (Foreign Keys)
    query = client.table("eventos_operativos").select(
        """
        id, fecha, guardia, estado_operativo, responsable_registro, observaciones,
        tiempo_improductivo, motivo_parada,
        labores!inner(nombre, nombre_geometrico),
        actividades_catalogo(nombre, unidad_produccion),
        consumo_recursos(
            cantidad,
            recursos_catalogo(nombre, unidad, tipo)
        ),
        resultados_fisicos(tipo_dato, cantidad_lograda)
        """
    ).gte("fecha", f_inicio_full).lte("fecha", f_fin_full)
    
    if labor_id:
        query = query.eq("labor_id", labor_id)
        
    query = query.order("fecha", desc=True)
    
    try:
        response = query.execute()
        # DEBUG: Si sale vacío, mirar la terminal para ver si imprimió algo antes
        if not response.data:
            print("⚠️ La consulta funcionó pero devolvió 0 filas.")
        return response.data
    except Exception as e:
        print(f"❌ ERROR EN CONSULTA REPORTES: {e}")
        # Si falla el join, intentamos traer data cruda para descartar
        return []