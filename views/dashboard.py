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
    Obtiene precios de mercado (Dólar y Oro).
    """
    try:
        # 1. Traer Dólar (PEN=X)
        dolar_ticker = yf.Ticker("PEN=X")
        dolar_data = dolar_ticker.history(period="1d")
        
        if dolar_data.empty: raise ValueError("Dólar vacío")
        precio_dolar = float(dolar_data['Close'].iloc[-1])

        # 2. Traer Oro (GC=F -> Futuros de Oro)
        oro_ticker = yf.Ticker("GC=F")
        oro_data = oro_ticker.history(period="1d")
        
        if oro_data.empty: raise ValueError("Oro vacío")
        precio_oro_usd_oz = float(oro_data['Close'].iloc[-1])

        # 3. Conversión
        precio_oro_pen_oz = precio_oro_usd_oz * precio_dolar
        precio_oro_pen_gramo = precio_oro_pen_oz / 31.1035

        return {
            "tc": round(precio_dolar, 3),
            "oz_usd": round(precio_oro_usd_oz, 2),
            "gr_pen": round(precio_oro_pen_gramo, 2),
            "status": True
        }

    except Exception as e:
        # Valores de respaldo si falla la conexión
        return {
            "tc": 3.75, 
            "oz_usd": 4500.00,
            "gr_pen": 487.00,
            "status": False
        }

def get_estado_mina():
    """
    Analiza la operación de HOY.
    Devuelve semáforo, KPIs y alertas.
    """
    client = get_supabase()
    hoy = date.today().isoformat()
    
    kpis = {"ton": 0, "mts": 0, "tal": 0, "costo": 0}
    estado = {"color": "#27AE60", "texto": "OPERACIÓN NORMAL", "icono": "🟢"} 
    alertas = []
    
    try:
        res_ev = client.table('eventos_operativos').select('*').eq('fecha', hoy).execute()
        eventos = res_ev.data
        
        if eventos:
            ids = [e['id'] for e in eventos]
            
            res_lab = client.table('labores').select('id, nombre').execute()
            mapa_labores = {l['id']: l['nombre'] for l in res_lab.data} if res_lab.data else {}

            paradas = [e for e in eventos if e.get('estado_operativo') == 'Parada Total']
            restringidos = [e for e in eventos if e.get('estado_operativo') == 'Restringido']
            
            if paradas:
                estado = {"color": "#C0392B", "texto": "PARADA TOTAL DETECTADA", "icono": "🔴"}
                for p in paradas:
                    lid = p.get('labor_id')
                    nombre_labor = mapa_labores.get(lid, f"Labor {lid}")
                    motivo = p.get('motivo_parada')
                    desc = motivo if motivo and motivo != "None" else "Sin descripción"
                    alertas.append(f"🔴 <b>{nombre_labor}</b>: {desc}")

            elif restringidos:
                estado = {"color": "#F39C12", "texto": "OPERACIÓN RESTRINGIDA", "icono": "🟡"}
                for r in restringidos:
                    lid = r.get('labor_id')
                    nombre_labor = mapa_labores.get(lid, f"Labor {lid}")
                    motivo = r.get('motivo_parada')
                    desc = motivo if motivo and motivo != "None" else "Restricción"
                    alertas.append(f"🟡 <b>{nombre_labor}</b>: {desc}")
            
            # KPIs Físicos
            res_fis = client.table('resultados_fisicos').select('*').in_('evento_id', ids).execute()
            df_fis = pd.DataFrame(res_fis.data)
            
            if not df_fis.empty:
                kpis["ton"] = df_fis[df_fis['tipo_dato'] == 'TONELAJE']['cantidad_lograda'].sum()
                kpis["mts"] = df_fis[df_fis['tipo_dato'] == 'AVANCE_M']['cantidad_lograda'].sum()
                kpis["tal"] = df_fis[df_fis['tipo_dato'].str.contains('TALADROS', na=False)]['cantidad_lograda'].sum()

            # Costos
            res_cons = client.table('consumo_recursos').select('cantidad, precio_snapshot').in_('evento_id', ids).execute()
            if res_cons.data:
                kpis["costo"] = sum([float(c['cantidad']) * float(c['precio_snapshot']) for c in res_cons.data])

    except Exception as e:
        print(f"Error Dashboard: {e}")

    return estado, kpis, alertas

# ==============================================================================
# 🎞️ COMPONENTES UI (ANIMACIÓN: WINCHE DE ARRASTRE)
# ==============================================================================
def mostrar_animacion_winche():
    """
    Muestra una animación CSS estilo 'Plano Técnico' de limpieza con winche.
    """
    st.markdown("""
        <style>
        /* CONTENEDOR PRINCIPAL */
        .winch-container {
            width: 100%; height: 120px; background-color: #F4F6F6;
            border: 1px solid #D5D8DC; border-radius: 8px;
            position: relative; overflow: hidden; margin-bottom: 20px;
            background-image: 
                linear-gradient(to right, rgba(21, 67, 96, 0.05) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(21, 67, 96, 0.05) 1px, transparent 1px);
            background-size: 20px 20px;
        }
        /* ETIQUETA TÉCNICA */
        .tech-label {
            position: absolute; top: 5px; left: 10px; font-family: 'Consolas', monospace;
            font-size: 0.7rem; color: #154360; opacity: 0.8; z-index: 10; font-weight: 700;
        }

        /* --- ELEMENTOS FIJOS --- */
        .floor { position: absolute; bottom: 15px; width: 100%; height: 3px; background: #154360; }
        
        /* El Motor del Winche */
        .winch-motor {
           position: absolute; left: 15px; bottom: 18px; width: 35px; height: 30px;
           background: #154360; border-radius: 4px; z-index: 2;
        }
        /* El Tambor giratorio */
        .winch-drum {
           position: absolute; left: 20px; bottom: 23px; width: 20px; height: 20px;
           border: 3px solid #F4F6F6; border-radius: 50%; border-left-color: #E74C3C; 
           animation: spin-drum 4s infinite linear; z-index: 3;
        }
        /* La Pila de Carga */
        .muck-pile {
            position: absolute; right: 5px; bottom: 18px; width: 70px; height: 40px;
            background: #95A5A6; 
            clip-path: polygon(0% 100%, 20% 70%, 40% 90%, 60% 50%, 80% 80%, 100% 100%);
        }

        /* --- ELEMENTOS MÓVILES --- */
        /* El Cable principal */
        .pull-cable {
            position: absolute; bottom: 30px; height: 2px; background: #154360;
            transform-origin: left center; z-index: 1;
            animation: cable-action 4s infinite ease-in-out;
        }
        /* La Pala (Scraper) */
        .scraper-bucket {
            position: absolute; bottom: 18px; width: 40px; height: 22px;
            border: 3px solid #154360; border-right: none; 
            background: transparent; z-index: 2;
            animation: scrape-cycle 4s infinite ease-in-out;
        }
        /* La Carga dentro de la pala (se pone roja) */
        .scraper-load {
            position: absolute; width: 25px; height: 15px; background: #E74C3C;
            bottom: 0; left: 5px; opacity: 0;
            animation: load-visibility 4s infinite ease-in-out;
        }

        /* --- KEYFRAMES --- */
        @keyframes spin-drum { 
            0% { transform: rotate(0deg); } 
            45% { transform: rotate(-720deg); } 
            55% { transform: rotate(-720deg); } 
            100% { transform: rotate(0deg); } 
        }
        @keyframes scrape-cycle {
            0%   { left: 80%; } 
            10%  { left: 80%; } 
            45%  { left: 55px; } 
            55%  { left: 55px; } 
            100% { left: 80%; } 
        }
        @keyframes load-visibility {
            0%   { opacity: 0; } 
            10%  { opacity: 0; } 
            12%  { opacity: 1; } 
            45%  { opacity: 1; } 
            48%  { opacity: 0; } 
            100% { opacity: 0; } 
        }
        @keyframes cable-action {
             0%  { left: 40px; width: 75%; } 
            10%  { left: 40px; width: 75%; }
            45%  { left: 40px; width: 25px; } 
            55%  { left: 40px; width: 25px; }
            100% { left: 40px; width: 75%; } 
        }
        </style>

        <div class="winch-container">
            <div class="tech-label">STATUS: LIMPIEZA DE FRENTE (WINCHE) // NV. 410</div>
            <div class="floor"></div>
            <div class="muck-pile"></div>
            <div class="winch-motor"></div>
            <div class="winch-drum"></div>
            <div class="pull-cable"></div>
            <div class="scraper-bucket">
                <div class="scraper-load"></div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 🎨 INTERFAZ (UI) - MODO MINA
# ==============================================================================
def mostrar_dashboard():
    # --- Datos de Sesión ---
    if 'user' not in st.session_state or not st.session_state.user:
        st.error("Sesión no iniciada")
        return

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
        html, body, [class*="css"] {{ font-family: 'Roboto', sans-serif; }}
        [data-testid="stSidebarNav"] {{ display: none !important; }}
        
        .top-bar {{
            display: flex; justify-content: space-between; align-items: center;
            border-bottom: 2px solid #E5E7E9; padding-bottom: 10px; margin-bottom: 15px;
        }}
        .sys-name {{ font-size: 1.5rem; font-weight: 900; color: #154360; letter-spacing: -1px; }}
        .sys-info {{ font-size: 0.9rem; color: #566573; font-weight: 600; text-align: right; }}
        
        .fin-row {{
            display: flex; gap: 15px; background: #F4F6F6; padding: 8px; 
            border-radius: 4px; border-left: 4px solid #F1C40F; align-items: center;
            font-family: 'Consolas', monospace;
        }}
        .fin-item {{ font-size: 0.9rem; color: #2C3E50; font-weight: 700; }}
        .fin-lbl {{ color: #7F8C8D; font-weight: 400; margin-right: 5px; }}

        .status-box {{
            background-color: {estado['color']}; color: white;
            padding: 15px; border-radius: 6px; text-align: center;
            font-size: 1.2rem; font-weight: 800; letter-spacing: 1px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
        }}

        .kpi-card {{
            background: white; border: 1px solid #D5D8DC; border-radius: 6px;
            padding: 15px; text-align: center;
        }}
        .kpi-val {{ font-size: 1.8rem; font-weight: 800; color: #17202A; line-height: 1; }}
        .kpi-tit {{ font-size: 0.75rem; color: #808B96; text-transform: uppercase; font-weight: 700; margin-top: 5px; }}
        
        .alert-item {{ 
            padding: 10px; border-left: 4px solid #C0392B; background: #FDEDEC; 
            margin-bottom: 5px; color: #922B21; font-weight: 500; font-size: 0.95rem;
        }}
    </style>
    """, unsafe_allow_html=True)

    # 1. ENCABEZADO
    st.markdown(f"""
    <div class="top-bar">
        <div class="sys-name">LITHOS V3</div>
        <div class="sys-info">
            {fecha_str} • GUARDIA {turno}<br>
            <span style="color:#154360;">{user_display}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. TICKER + BOTÓN
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
        if st.button("🔄", help="Actualizar Cotizaciones", use_container_width=True):
            st.session_state['data_mercado'] = get_market_data()
            st.rerun()

    # 3. SEMÁFORO
    st.markdown(f"""
    <div class="status-box">
        {estado['icono']} {estado['texto']}
    </div>
    """, unsafe_allow_html=True)

    # 4. KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['ton']:,.0f}</div><div class="kpi-tit">Producción (Ton)</div></div>""", unsafe_allow_html=True)
    with k2: st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['mts']:,.1f}</div><div class="kpi-tit">Avance (m)</div></div>""", unsafe_allow_html=True)
    with k3: st.markdown(f"""<div class="kpi-card"><div class="kpi-val">{kpis['tal']:,.0f}</div><div class="kpi-tit">Taladros</div></div>""", unsafe_allow_html=True)
    with k4: st.markdown(f"""<div class="kpi-card"><div class="kpi-val">S/.{kpis['costo']/1000:,.1f}k</div><div class="kpi-tit">Costo Est.</div></div>""", unsafe_allow_html=True)

    st.write("") 

    # 5. ANIMACIÓN WINCHE
    mostrar_animacion_winche()

    st.write("")

    # 6. ALERTAS Y ACCIONES
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