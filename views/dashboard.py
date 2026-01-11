import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
from db.supabase_client import get_supabase

# ==============================================================================
# 🧠 MOTOR DE DATOS (BACKEND)
# ==============================================================================

def get_market_data():
    """
    Tu código adaptado para devolver el formato que necesita el Dashboard.
    """
    try:
        # 1. Traer Dólar (PEN=X)
        dolar_ticker = yf.Ticker("PEN=X")
        dolar_data = dolar_ticker.history(period="1d")
        
        # Validación de seguridad
        if dolar_data.empty: raise ValueError("Dólar vacío")
        precio_dolar = float(dolar_data['Close'].iloc[-1])

        # 2. Traer Oro (GC=F -> Futuros de Oro)
        oro_ticker = yf.Ticker("GC=F")
        oro_data = oro_ticker.history(period="1d")
        
        # Validación de seguridad
        if oro_data.empty: raise ValueError("Oro vacío")
        precio_oro_usd_oz = float(oro_data['Close'].iloc[-1])

        # 3. Conversión (Tu fórmula)
        # 1 Onza Troy = 31.1035 gramos
        precio_oro_pen_oz = precio_oro_usd_oz * precio_dolar
        precio_oro_pen_gramo = precio_oro_pen_oz / 31.1035

        # RETORNO: Devolvemos un diccionario (no una tupla) para que el Dashboard lo entienda
        return {
            "tc": round(precio_dolar, 3),
            "oz_usd": round(precio_oro_usd_oz, 2),
            "gr_pen": round(precio_oro_pen_gramo, 2),
            "status": True
        }

    except Exception as e:
        # Si falla, usamos valores por defecto para que no se caiga la presentación
        print(f"Error Yahoo: {e}")
        return {
            "tc": 3.75, 
            "oz_usd": 4500.00, # Ajustado a precio real mercado
            "gr_pen": 487.00,  # Ajustado a precio real mercado
            "status": False
        }

def get_estado_mina():
    """
    Analiza la operación de HOY.
    Devuelve: Semáforo (Color), KPIs, y Alertas con NOMBRES REALES.
    """
    client = get_supabase()
    hoy = date.today().isoformat()
    
    # Estructura base
    kpis = {"ton": 0, "mts": 0, "tal": 0, "costo": 0}
    estado = {"color": "#27AE60", "texto": "OPERACIÓN NORMAL", "icono": "🟢"} 
    alertas = []
    
    try:
        # 1. Traer eventos de HOY
        res_ev = client.table('eventos_operativos').select('*').eq('fecha', hoy).execute()
        eventos = res_ev.data
        
        if eventos:
            ids = [e['id'] for e in eventos]
            
            # --- CORRECCIÓN CLAVE: Obtener mapa de nombres de labores ---
            res_lab = client.table('labores').select('id, nombre').execute()
            mapa_labores = {l['id']: l['nombre'] for l in res_lab.data} if res_lab.data else {}

            # 2. Análisis de Estado (Semáforo y Alertas)
            paradas = [e for e in eventos if e.get('estado_operativo') == 'Parada Total']
            restringidos = [e for e in eventos if e.get('estado_operativo') == 'Restringido']
            
            if paradas:
                estado = {"color": "#C0392B", "texto": "PARADA TOTAL DETECTADA", "icono": "🔴"}
                for p in paradas:
                    lid = p.get('labor_id')
                    nombre_labor = mapa_labores.get(lid, f"Labor {lid}")
                    motivo = p.get('motivo_parada')
                    desc_motivo = motivo if motivo and motivo != "None" else "Parada sin descripción"
                    alertas.append(f"🔴 <b>{nombre_labor}</b>: {desc_motivo}")

            elif restringidos:
                estado = {"color": "#F39C12", "texto": "OPERACIÓN RESTRINGIDA", "icono": "🟡"}
                for r in restringidos:
                    lid = r.get('labor_id')
                    nombre_labor = mapa_labores.get(lid, f"Labor {lid}")
                    motivo = r.get('motivo_parada')
                    desc_motivo = motivo if motivo and motivo != "None" else "Restricción operativa"
                    alertas.append(f"🟡 <b>{nombre_labor}</b>: {desc_motivo}")
            
            # 3. Calcular KPIs (Sumatoria)
            res_fis = client.table('resultados_fisicos').select('*').in_('evento_id', ids).execute()
            df_fis = pd.DataFrame(res_fis.data)
            
            if not df_fis.empty:
                kpis["ton"] = df_fis[df_fis['tipo_dato'] == 'TONELAJE']['cantidad_lograda'].sum()
                kpis["mts"] = df_fis[df_fis['tipo_dato'] == 'AVANCE_M']['cantidad_lograda'].sum()
                kpis["tal"] = df_fis[df_fis['tipo_dato'].str.contains('TALADROS', na=False)]['cantidad_lograda'].sum()

            # 4. Calcular Costos
            res_cons = client.table('consumo_recursos').select('cantidad, precio_snapshot').in_('evento_id', ids).execute()
            if res_cons.data:
                costo_total = sum([float(c['cantidad']) * float(c['precio_snapshot']) for c in res_cons.data])
                kpis["costo"] = costo_total

    except Exception as e:
        print(f"Error Dashboard: {e}") # Debug interno

    return estado, kpis, alertas

# ==============================================================================
# 🎞️ COMPONENTES UI (ANIMACIONES, ETC.) - [NUEVO]
# ==============================================================================
def mostrar_animacion_perforacion():
    """
    Muestra una animación CSS estilo 'Plano Técnico' de una perforación.
    """
    st.markdown("""
        <style>
        /* CONTENEDOR PRINCIPAL */
        .drill-container {
            width: 100%; height: 120px; background-color: #F4F6F6;
            border: 1px solid #D5D8DC; border-radius: 8px;
            position: relative; overflow: hidden; margin-bottom: 20px;
        }
        /* ETIQUETA TÉCNICA */
        .tech-label {
            position: absolute; top: 5px; left: 10px; font-family: 'Consolas', monospace;
            font-size: 0.7rem; color: #154360; opacity: 0.6; z-index: 10;
        }
        /* LA ROCA (El bloque derecho) */
        .rock-face {
            position: absolute; right: 0; top: 20px; width: 60%; height: 80px;
            background: repeating-linear-gradient(45deg, #EAEDED, #EAEDED 5px, #D5D8DC 5px, #D5D8DC 10px);
            border-left: 3px solid #154360;
        }
        /* EL TALADRO (La máquina a la izquierda) */
        .jackleg-body {
            position: absolute; left: 20px; top: 50px; width: 40px; height: 25px;
            border: 2px solid #154360; background-color: transparent; animation: vibrar 0.1s infinite;
        }
        /* La pata del Jackleg */
        .jackleg-leg {
            position: absolute; left: 30px; top: 75px; width: 3px; height: 40px;
            background-color: #154360; transform: rotate(-30deg); transform-origin: top center;
            animation: vibrar 0.1s infinite;
        }
        /* EL BARRENO (La línea que perfora) */
        .drill-steel {
            position: absolute; left: 60px; top: 60px; height: 4px; background-color: #E74C3C;
            width: 0%; animation: perforar 4s infinite linear, vibrar-acero 0.1s infinite;
        }

        /* --- ANIMACIONES (KEYFRAMES) --- */
        @keyframes vibrar {
            0% { transform: translate(0, 0); } 25% { transform: translate(1px, 1px); }
            50% { transform: translate(0, -1px); } 75% { transform: translate(-1px, 0); } 100% { transform: translate(0, 0); }
        }
        @keyframes perforar {
            0% { width: 0%; left: 60px; opacity: 1;} 70% { width: 50%; left: 60px; opacity: 1;}
            80% { width: 50%; left: 60px; opacity: 0;} 81% { width: 0%; left: 60px; opacity: 0;} 100% { width: 0%; left: 60px; opacity: 1;}
        }
        @keyframes vibrar-acero {
             0% { margin-top: 0px; } 50% { margin-top: 1px; } 100% { margin-top: 0px; }
        }
        </style>

        <div class="drill-container">
            <div class="tech-label">STATUS: PERFORACIÓN EN CURSO // Nv. 340</div>
            <div class="rock-face"></div> <div class="jackleg-body"></div> <div class="jackleg-leg"></div> <div class="drill-steel"></div> </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 🎨 INTERFAZ (UI) - MODO MINA
# ==============================================================================
def mostrar_dashboard():
    # --- Datos de Sesión ---
    u = st.session_state.user
    user_display = f"{u.get('nombre_completo', 'Usuario').split()[0]} | {u.get('cargo', 'Staff')}"
    rol = u.get('rol_sistema', 'LECTOR')
    
    ahora = datetime.now()
    turno = "NOCHE" if (ahora.hour >= 18 or ahora.hour < 6) else "DÍA"
    fecha_str = ahora.strftime("%d-%m-%Y")
    
    # --- Lógica de Carga de Datos Financieros con Cache ---
    if 'data_mercado' not in st.session_state:
        st.session_state['data_mercado'] = get_market_data()
    
    # Usamos la variable de sesión en lugar de llamar a la función directo
    fin = st.session_state['data_mercado']

    estado, kpis, lista_alertas = get_estado_mina()
    
    # --- CSS INDUSTRIAL ---
    st.markdown(f"""
    <style>
        /* Tipografía y Reset */
        html, body, [class*="css"] {{ font-family: 'Roboto', sans-serif; }}
        [data-testid="stSidebarNav"] {{ display: none !important; }}
        
        /* 1. Encabezado Compacto */
        .top-bar {{
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 2px solid #E5E7E9; padding-bottom: 10px; margin-bottom: 15px;
        }}
        .sys-name {{ font-size: 1.5rem; font-weight: 900; color: #154360; letter-spacing: -1px; }}
        .sys-info {{ font-size: 0.9rem; color: #566573; font-weight: 600; text-align: right; }}
        
        /* 2. Ticker Financiero */
        .fin-row {{
            display: flex; gap: 15px;
            font-family: 'Consolas', monospace;
            background: #F4F6F6; padding: 8px; border-radius: 4px; border-left: 4px solid #F1C40F;
            align-items: center; /* Centrar verticalmente */
        }}
        .fin-item {{ font-size: 0.9rem; color: #2C3E50; font-weight: 700; }}
        .fin-lbl {{ color: #7F8C8D; font-weight: 400; margin-right: 5px; }}

        /* 3. Semáforo Operativo */
        .status-box {{
            background-color: {estado['color']}; color: white;
            padding: 15px; border-radius: 6px; text-align: center;
            font-size: 1.2rem; font-weight: 800; letter-spacing: 1px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}

        /* 4. KPIs Cards */
        .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px; }}
        .kpi-card {{
            background: white; border: 1px solid #D5D8DC; border-radius: 6px;
            padding: 15px; text-align: center;
        }}
        .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #17202A; line-height: 1; }}
        .kpi-tit {{ font-size: 0.75rem; color: #808B96; text-transform: uppercase; font-weight: 700; margin-top: 5px; }}
        
        /* 5. Alertas */
        .alert-item {{ 
            padding: 10px; border-left: 4px solid #C0392B; background: #FDEDEC; 
            margin-bottom: 5px; color: #922B21; font-weight: 500; font-size: 0.95rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # 1️⃣ ENCABEZADO LIMPIO
    # ==========================================================================
    st.markdown(f"""
    <div class="top-bar">
        <div class="sys-name">LITHOS V3</div>
        <div class="sys-info">
            {fecha_str} • GUARDIA {turno}<br>
            <span style="color:#154360;">{user_display}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # 2️⃣ INDICADORES FINANCIEROS (INTEGRADO CON BOTÓN)
    # ==========================================================================
    # Usamos columnas para poner el botón al lado de la barra de precios
    col_ticker, col_btn = st.columns([8, 1])
    
    with col_ticker:
        st.markdown(f"""
        <div class="fin-row">
            <div class="fin-item"><span class="fin-lbl">TC:</span> S/. {fin['tc']:.3f}</div>
            <div class="fin-item"><span class="fin-lbl">Au (gr):</span> S/. {fin['gr_pen']:.2f}</div>
            <div class="fin-item"><span class="fin-lbl">Au (oz):</span> $ {fin['oz_usd']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_btn:
        # Botón pequeño de refresco
        if st.button("🔄", help="Actualizar Cotizaciones", use_container_width=True):
            st.session_state['data_mercado'] = get_market_data()
            st.rerun()

    # ==========================================================================
    # 3️⃣ ESTADO GENERAL (SEMÁFORO)
    # ==========================================================================
    st.markdown(f"""
    <div class="status-box">
        {estado['icono']} {estado['texto']}
    </div>
    """, unsafe_allow_html=True)

    # ==========================================================================
    # 4️⃣ KPIs CLAVE
    # ==========================================================================
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['ton']:,.0f}</div><div class="kpi-tit">Producción (Ton)</div></div>""", unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['mts']:,.1f}</div><div class="kpi-tit">Avance (m)</div></div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['tal']:,.0f}</div><div class="kpi-tit">Taladros</div></div>""", unsafe_allow_html=True)
    with k4:
        st.markdown(f"""<div class="kpi-card"><div class="kpi-val">S/.{kpis['costo']/1000:,.1f}k</div><div class="kpi-tit">Costo Est.</div></div>""", unsafe_allow_html=True)

    st.write("") 

    # ==========================================================================
    # [NUEVO] 🎞️ ANIMACIÓN DE OPERACIÓN (Insertada aquí)
    # ==========================================================================
    mostrar_animacion_perforacion()

    st.write("")

    # ==========================================================================
    # 5️⃣ ALERTAS & ACCIÓN RÁPIDA
    # ==========================================================================
    c_alertas, c_acciones = st.columns([1.5, 1])

    with c_alertas:
        st.markdown("**🔔 Novedades del Turno**")
        if lista_alertas:
            for alerta in lista_alertas:
                st.markdown(f'<div class="alert-item">{alerta}</div>', unsafe_allow_html=True)
        else:
            st.info("Sin incidentes reportados hasta el momento.")

    with c_acciones:
        st.markdown("**⚡ Acciones**")
        
        if rol in ['ADMIN', 'OPERATIVO']:
            if st.button("➕ REGISTRAR EVENTO", type="primary", use_container_width=True):
                st.switch_page("pages/1_registro.py")
            st.markdown("<div style='margin-bottom:10px'></div>", unsafe_allow_html=True)
        else:
            st.button("➕ Registro (Solo Lectura)", disabled=True, use_container_width=True)

        c_a1, c_a2 = st.columns(2)
        with c_a1:
            if st.button("Consultas", use_container_width=True): st.switch_page("pages/2_consultas.py")
        with c_a2:
            if st.button("Indicadores", use_container_width=True): st.switch_page("pages/3_indicadores.py")
        
        if rol == 'ADMIN':
             if st.button("Configuración", use_container_width=True): st.switch_page("pages/4_configuracion.py")

    with st.sidebar:
        if st.button("Cerrar Sesión"):
            st.session_state.user = None
            st.rerun()