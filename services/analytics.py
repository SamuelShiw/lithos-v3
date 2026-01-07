import pandas as pd
from db.supabase_client import get_supabase

class AnalyticsService:
    """
    Motor de cálculo de KPIs. 
    Descarga datos crudos y los transforma en DataFrames de Pandas 
    para facilitar métricas y gráficos.
    """

    @staticmethod
    def get_dataframe_maestro(fecha_ini, fecha_fin, labor_id=None, guardia=None, actividades=None):
        """
        Obtiene TODO lo ocurrido en el rango y devuelve 3 DataFrames conectados:
        1. df_eventos (Cabeceras)
        2. df_prod (Resultados Físicos)
        3. df_costos (Consumos valorizados)
        """
        client = get_supabase()
        
        # 1. Query Base de Eventos
        query = client.table("eventos_operativos").select(
            "id, fecha, guardia, labor_id, actividad_id, labores(nombre), actividades_catalogo(nombre)"
        ).gte("fecha", fecha_ini).lte("fecha", fecha_fin)
        
        if labor_id: query = query.eq("labor_id", labor_id)
        if guardia: query = query.eq("guardia", guardia)
        
        res_ev = query.execute()
        if not res_ev.data: return None, None, None
        
        df_ev = pd.DataFrame(res_ev.data)
        # Limpieza de nombres
        df_ev['Labor'] = df_ev['labores'].apply(lambda x: x['nombre'])
        df_ev['Actividad'] = df_ev['actividades_catalogo'].apply(lambda x: x['nombre'])
        df_ev['fecha'] = pd.to_datetime(df_ev['fecha'])
        
        # Filtro de Actividad (Post-query porque Supabase filtra por ID exacto, y aquí queremos nombres)
        if actividades:
            df_ev = df_ev[df_ev['Actividad'].isin(actividades)]
            if df_ev.empty: return None, None, None

        ids_eventos = df_ev['id'].tolist()

        # 2. Query Resultados (Producción)
        res_prod = client.table("resultados_fisicos").select("*").in_("evento_id", ids_eventos).execute()
        df_prod = pd.DataFrame(res_prod.data) if res_prod.data else pd.DataFrame(columns=['evento_id', 'tipo_dato', 'cantidad_lograda'])

        # 3. Query Consumos (Costos)
        res_cons = client.table("consumo_recursos").select("*, recursos_catalogo(nombre, tipo, unidad_medida)").in_("evento_id", ids_eventos).execute()
        df_cons = pd.DataFrame(res_cons.data) if res_cons.data else pd.DataFrame(columns=['evento_id', 'cantidad', 'precio_snapshot'])
        
        if not df_cons.empty:
            df_cons['Costo_Total'] = df_cons['cantidad'] * df_cons['precio_snapshot']
            df_cons['Recurso'] = df_cons['recursos_catalogo'].apply(lambda x: x['nombre'])
            df_cons['Tipo_Recurso'] = df_cons['recursos_catalogo'].apply(lambda x: x['tipo'])

        return df_ev, df_prod, df_cons

    @staticmethod
    def calcular_kpis_tarjetas(df_ev, df_prod, df_cons):
        """Calcula los números grandes para las tarjetas"""
        if df_ev is None: return {}

        # Producción Total
        ton_total = df_prod[df_prod['tipo_dato'] == 'TONELAJE']['cantidad_lograda'].sum()
        mts_total = df_prod[df_prod['tipo_dato'] == 'AVANCE_M']['cantidad_lograda'].sum()
        tal_total = df_prod[df_prod['tipo_dato'] == 'TALADROS']['cantidad_lograda'].sum()
        
        # Eficiencia (Promedios por Turno)
        num_turnos = df_ev['id'].nunique()
        ton_turno = ton_total / num_turnos if num_turnos > 0 else 0
        mts_turno = mts_total / num_turnos if num_turnos > 0 else 0

        # Costos
        costo_total = df_cons['Costo_Total'].sum() if not df_cons.empty else 0
        costo_metro = costo_total / mts_total if mts_total > 0 else 0
        costo_ton = costo_total / ton_total if ton_total > 0 else 0

        # Consumo Técnico (Ej: Explosivo / Metro)
        # Filtramos solo explosivos
        if not df_cons.empty:
            df_explo = df_cons[df_cons['Tipo_Recurso'] == 'INSUMO'] # Simplificación, ideal filtrar por nombre
            gasto_explo = df_explo['Costo_Total'].sum()
            costo_explo_m = gasto_explo / mts_total if mts_total > 0 else 0
        else:
            costo_explo_m = 0

        return {
            "prod_ton": ton_total,
            "prod_mts": mts_total,
            "prod_tal": tal_total,
            "efi_ton_turno": ton_turno,
            "efi_mts_turno": mts_turno,
            "fin_costo_total": costo_total,
            "fin_costo_m": costo_metro,
            "fin_costo_ton": costo_ton,
            "tec_explo_m": costo_explo_m
        }

    @staticmethod
    def preparar_series_tiempo(df_ev, df_prod, frecuencia='D'):
        """Agrupa datos por tiempo (D=Día, W=Semana, M=Mes) para gráficos"""
        if df_ev is None or df_prod.empty: return pd.DataFrame()

        # Unimos fechas con producción
        df_merge = pd.merge(df_ev[['id', 'fecha']], df_prod, left_on='id', right_on='evento_id')
        
        # Pivoteamos para tener columnas: Fecha | AVANCE_M | TONELAJE
        df_pivot = df_merge.pivot_table(
            index='fecha', 
            columns='tipo_dato', 
            values='cantidad_lograda', 
            aggfunc='sum'
        ).fillna(0)
        
        # Resampleo temporal
        df_resampled = df_pivot.resample(frecuencia).sum()
        return df_resampled