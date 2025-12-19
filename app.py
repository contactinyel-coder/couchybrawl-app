import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="CouchyBrawl", layout="wide", initial_sidebar_state="expanded")

# ANCLA PARA IR ARRIBA
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)

st.title("🏆 CouchyBrawl")
st.caption("Tu asistente táctico para subir a Maestros")

# ==========================================
# 🔑 ZONA DE CONFIGURACIÓN DE CLAVES
# ==========================================

# 1. Pon tu API KEY aquí abajo (borra lo que hay y pega la tuya):
API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImIxMGI2N2QxLTBmYTQtNGE0MS04ZWQxLWRhYWIxZmYyOWIwYyIsImlhdCI6MTc2NjE1OTIwOSwic3ViIjoiZGV2ZWxvcGVyL2Q1MGFlYWZlLTA0MmQtMWE5NS04MzBhLTNhMzVmM2JiZjQ0OCIsInNjb3BlcyI6WyJicmF3bHN0YXJzIl0sImxpbWl0cyI6W3sidGllciI6ImRldmVsb3Blci9zaWx2ZXIiLCJ0eXBlIjoidGhyb3R0bGluZyJ9LHsiY2lkcnMiOlsiMTkxLjk3LjI0Ny4xNTYiXSwidHlwZSI6ImNsaWVudCJ9XX0.00qHwOHTLfGDwvTfE3meI3jOuCE1yV12_ld1HffWC0Wyk_TqofygrBrWIOebLX2GEPp2fzRs6AyIIdkjMfnRMw"

# 2. Lógica de sobreescritura automática (Si estás en la Nube, usa los Secrets)
try:
    if "BRAWL_API_KEY" in st.secrets:
        API_KEY = st.secrets["BRAWL_API_KEY"]
except:
    pass

# Verificación de seguridad
if len(API_KEY) < 20:
    st.error("⚠️ ALERTA: No has pegado tu API KEY en la línea 20 del código.")
    st.stop()

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://api.brawlstars.com/v1"

# --- CONFIGURACIÓN GOOGLE SHEETS (AUTODETECTABLE) ---
def conectar_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    # Intentamos primero leer de la Nube (Secrets)
    try:
        # Si esto funciona, estamos en Streamlit Cloud
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except:
        # Si falla, asumimos que estamos en LOCAL y buscamos el archivo
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        except FileNotFoundError:
            st.error("❌ Error crítico: No se encuentra 'secrets.json' y no hay configuración de Nube.")
            st.stop()
    
    client = gspread.authorize(creds)
    sheet = client.open("Base_Datos_Brawl").sheet1
    return sheet

# --- LISTA DE MAPAS ACTUALIZADA ---
MAPAS_RANKED = [
    "Belle's Rock", "Bridge Too Far", "Center Stage", "Deathcap Trap", "Double Swoosh",
    "Dry Season", "Dueling Beetles", "Excel", "Flaring Phoenix", "Flowing Springs",
    "Gem Fort", "Goldarm Gulch", "Grass Knot", "Hard Rock Mine", "Hideout",
    "Hot Potato", "In the Liminal", "Infinite Doom", "Kaboom Canyon", "Layer Cake",
    "Massive Attack", "New Horizons", "Open Business", "Out in the Open", "Parallel Plays",
    "Pinball Dreams", "Quick Travel", "Ring of Fire", "Safe Zone", "Shooting Star",
    "Sneaky Fields", "Spiraling Out", "Triple Dribble", "Undermine"
]

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_global_data():
    try:
        df = pd.read_csv('datos_ranked_raw.csv')
        df['map'] = df['map'].astype(str).str.strip()
        df = df[df['map'].isin(MAPAS_RANKED)]
        if 'ally_1' not in df.columns:
            df['ally_1'] = 'None'; df['ally_2'] = 'None'
        return df
    except FileNotFoundError:
        return None

df = load_global_data()

if df is None:
    st.error("❌ Falta el archivo 'datos_ranked_raw.csv'. Ejecuta el recolector primero.")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def limpiar_seleccion():
    st.session_state['enemigos_key'] = []
    st.session_state['aliados_key'] = []

# --- 2. GESTIÓN CLOUD (FILTRO DE MAPAS RANKED AÑADIDO) ---
def actualizar_historial_nube(player_tag):
    clean_tag = player_tag.replace("#", "").upper()
    
    # Conexión Sheets
    try:
        hoja = conectar_google_sheets()
    except Exception as e:
        st.error(f"❌ Error conectando a Google Sheets: {e}")
        return pd.DataFrame()

    # Conexión API Brawl Stars
    url = f"{BASE_URL}/players/%23{clean_tag}/battlelog"
    nuevos = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            if not items:
                st.warning("⚠️ La API respondió OK, pero no trajo partidas (¿Jugaste hace poco?)")

            for item in items:
                battle = item.get('battle', {})
                event = item.get('event', {})
                battle_time = item.get('battleTime')
                map_name = event.get('map') # Capturamos nombre del mapa
                
                # --- NUEVO FILTRO DE MAPA RANKED ---
                # Si el mapa NO está en nuestra lista de Ranked, lo saltamos.
                if map_name not in MAPAS_RANKED:
                    continue 

                if 'event' in item and 'map' in item['event']:
                    result = battle.get('result', 'draw')
                    found_brawler = None
                    
                    # Buscar jugador en Teams (3v3)
                    if 'teams' in battle:
                        for team in battle['teams']:
                            for p in team:
                                if p['tag'].replace("#", "").upper() == clean_tag:
                                    found_brawler = p['brawler']['name']
                                    break
                            if found_brawler: break
                    
                    # Buscar jugador en Solo (Showdown)
                    elif 'players' in battle:
                        for p in battle['players']:
                            if p['tag'].replace("#", "").upper() == clean_tag:
                                found_brawler = p['brawler']['name']
                                break

                    if found_brawler:
                        win = 1 if result == 'victory' else 0
                        if result == 'draw': continue
                        nuevos.append([clean_tag, battle_time, map_name, found_brawler, win])
        
        elif response.status_code == 404:
            st.error(f"❌ Jugador no encontrado. Verifica el Tag: #{clean_tag}")
            return pd.DataFrame()
        elif response.status_code == 403:
            st.error("❌ Error de Permisos (403). Tu API KEY es incorrecta o expiró.")
            return pd.DataFrame()
        else:
            st.error(f"❌ Error API Brawl Stars: Código {response.status_code}")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"❌ Error de conexión: {e}")
        return pd.DataFrame()

    # Guardado en Sheets
    if nuevos:
        actuales = hoja.get_all_records()
        df_nube = pd.DataFrame(actuales)
        existentes = set()
        if not df_nube.empty:
            existentes = set(zip(df_nube['player_tag'].astype(str), df_nube['battle_time'].astype(str)))
        
        subir = [f for f in nuevos if (str(f[0]), str(f[1])) not in existentes]
        
        if subir:
            hoja.append_rows(subir)
            st.toast(f"☁️ Guardadas {len(subir)} partidas RANKED nuevas.", icon="✅")
        else:
            st.toast("✅ Sin novedades (partidas ya guardadas).", icon="ℹ️")
    else:
        # Mensaje modificado para aclarar por qué no se guardó nada
        st.toast("✅ Sincronizado (No hay partidas RANKED nuevas en el log).", icon="ℹ️")
            
    final = hoja.get_all_records()
    df_t = pd.DataFrame(final)
    if not df_t.empty: return df_t[df_t['player_tag'] == clean_tag]
    return pd.DataFrame()

# --- 3. BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configuración")
    st.metric(label="📚 Base de Datos Global", value=f"{len(df):,}")
    
    mapa_seleccionado = st.selectbox("📍 Mapa:", sorted(df['map'].unique()))
    if mapa_seleccionado:
        count_mapa = len(df[df['map'] == mapa_seleccionado])
        st.caption(f"📊 Partidas analizadas aquí: **{count_mapa}**")
    
    st.divider()
    
    st.subheader("👤 Tu Perfil")
    user_tag = st.text_input("Player Tag (#...)", placeholder="#...")
    if st.button("🔄 Sincronizar Historial"):
        if len(user_tag) < 3: st.error("Tag corto")
        else:
            with st.spinner("Conectando con CouchyBrawl Cloud..."):
                mis_datos = actualizar_historial_nube(user_tag)
                if not mis_datos.empty:
                    st.session_state['my_history'] = mis_datos
                    st.success("¡Historial cargado!")
    
    if 'my_history' in st.session_state and not st.session_state['my_history'].empty:
        hist = st.session_state['my_history']
        st.caption(f"☁️ Tus partidas: **{len(hist)}**")
        hist_sorted = hist.sort_values(by='battle_time', ascending=False)
        preview = hist_sorted.head(5).copy()[['map', 'my_brawler', 'result']]
        preview['result'] = preview['result'].apply(lambda x: "✅" if x == 1 else "❌")
        preview.columns = ['Mapa', 'Brawler', 'Res']
        st.dataframe(preview, hide_index=True, use_container_width=True)
    else:
        st.info("Ingresa tu Tag para ver tus estadísticas.")

# --- 4. LAYOUT PRINCIPAL ---
if mapa_seleccionado:
    df_mapa = df[df['map'] == mapa_seleccionado]
    meta_mapa = df_mapa.groupby('my_brawler').agg(
        win_rate_mapa=('result', 'mean'),
        partidas_mapa=('result', 'count')
    ).reset_index()
    meta_mapa = meta_mapa[meta_mapa['partidas_mapa'] >= 3]
else:
    meta_mapa = pd.DataFrame()

bloque_izq, bloque_der = st.columns([2, 1.5]) 

# --- A. BLOQUE IZQUIERDO ---
with bloque_izq:
    col_btn, _ = st.columns([1, 4])
    with col_btn:
        st.button("🗑️ Limpiar Todo", on_click=limpiar_seleccion)

    col_enemigos, col_aliados = st.columns(2)
    with col_enemigos:
        st.markdown("### ⚔️ Enemigos")
        enemigos = st.multiselect("Ellos:", sorted(df['my_brawler'].unique()), max_selections=3, key='enemigos_key')
    with col_aliados:
        st.markdown("### 🤝 Tu Equipo")
        aliados = st.multiselect("Tu aliado:", sorted(df['my_brawler'].unique()), max_selections=2, key='aliados_key')
    
    st.markdown("---")
    
    with st.expander("📖 Cómo usar CouchyBrawl", expanded=False):
        st.markdown("""
        **Guía Rápida:**
        1. **📍 Mapa:** Selecciónalo.
        2. **⚔️ Draft:** Ingresa brawlers enemigos (descubre sus counters) / ingresa tus aliados (descubre sus sinergias).
        3. **🧠 Análisis:** Revisa la tabla ordenada por Meta y Puntuación.
        4. **🚫 Fase de Bans:** La App no tiene botón de "Bans", pero tú usa tu cerebro: Si la App dice que Piper y Nani son las mejores (tienen el puntaje más alto), **BANÉALAS** si no tienes el primer pick, o déjalas libres si tú vas a elegir primero.
        
        **Leyenda:**
        * **💎 Meta:** Brawlers muy populares (Tier S).
        * **⚠️ Bajo:** Pocos datos. Arriesgado.
        * **🔥/💀 Tu rendimiento personal:** Agrega tu Player Tag y "sincroniza el historial" para conocer tus puntos fuertes y débiles.
        
        **⚠️ ¡ATENCIÓN!** Hay un límite de registro de partidas en el juego: ¡son tus últimas **25 partidas jugadas**! Sé inteligente y carga/sincroniza tus partidas cada vez que juegues Ranked para ir acumulando datos en tu historial.
        """)

# --- B. BLOQUE DERECHO ---
with bloque_der:
    col_titulo, col_ajustes = st.columns([4, 1])
    
    with col_titulo:
        st.markdown("### 🧠 Recomendaciones")
    
    with col_ajustes:
        with st.popover("⚙️ Ajustes", help="Configurar cálculo matemático"):
            st.markdown("**Calibración IA**")
            C = st.slider(
                "Suavizado (C)", 
                min_value=0, 
                max_value=200, 
                value=100, 
                step=10,
                help="Partidas 'fantasma' añadidas. Mayor valor = Prioriza brawlers con muchas partidas."
            )
            st.caption(f"Valor actual: {C}")

    if not meta_mapa.empty:
        recomendaciones = meta_mapa.copy()
        
        # 1. CÁLCULO DE SCORE
        M = 0.5
        recomendaciones['wr_ajustado'] = ((recomendaciones['win_rate_mapa'] * recomendaciones['partidas_mapa'] + C*M) / (recomendaciones['partidas_mapa'] + C))
        
        recomendaciones['score_counter'] = 0.5
        if enemigos:
            scores = []
            for b in recomendaciones['my_brawler']:
                vs = df[(df['my_brawler'] == b) & (df['enemy_brawler'].isin(enemigos))]
                scores.append((vs['result'].sum() + 1) / (len(vs) + 2) if len(vs)>0 else 0.5)
            recomendaciones['score_counter'] = scores
            
        recomendaciones['score_synergy'] = 0.5
        if aliados:
            scores_syn = []
            for b in recomendaciones['my_brawler']:
                syn = df[(df['my_brawler'] == b) & ((df['ally_1'].isin(aliados)) | (df['ally_2'].isin(aliados)))]
                scores_syn.append((syn['result'].sum() + 1) / (len(syn) + 2) if len(syn)>0 else 0.5)
            recomendaciones['score_synergy'] = scores_syn

        if aliados and enemigos: W_MAP=0.35; W_CNT=0.35; W_SYN=0.30
        elif enemigos: W_MAP=0.45; W_CNT=0.55; W_SYN=0.0
        elif aliados: W_MAP=0.50; W_CNT=0.0; W_SYN=0.50
        else: W_MAP=1.0; W_CNT=0.0; W_SYN=0.0
            
        recomendaciones['score_final'] = ((recomendaciones['wr_ajustado'] * W_MAP) + (recomendaciones['score_counter'] * W_CNT) + (recomendaciones['score_synergy'] * W_SYN)) * 100
        
        # 2. LÓGICA DE TIERS
        max_picks = recomendaciones['partidas_mapa'].max()
        if pd.isna(max_picks) or max_picks == 0: max_picks = 1 
        step = max_picks / 4
        
        def asignar_tier(picks):
            if picks >= step * 3: return 4
            elif picks >= step * 2: return 3
            elif picks >= step: return 2
            else: return 1

        recomendaciones['Tier'] = recomendaciones['partidas_mapa'].apply(asignar_tier)
        
        # 3. FILTRO DRAFT
        brawlers_no_disponibles = enemigos + aliados
        if brawlers_no_disponibles:
            recomendaciones = recomendaciones[~recomendaciones['my_brawler'].isin(brawlers_no_disponibles)]
        
        # ORDENAR
        top_picks = recomendaciones.sort_values(by=['Tier', 'score_final'], ascending=[False, False])
        
        # 4. MOSTRAR TABLA
        personal_history = st.session_state.get('my_history', pd.DataFrame())
        
        tabla_data = []
        
        for posicion, (index, row) in enumerate(top_picks.iterrows()):
            brawler_name = row['my_brawler']
            score = row['score_final']
            picks = row['partidas_mapa']
            tier = row['Tier']
            
            if tier == 4: tier_label = "💎 Meta"
            elif tier == 3: tier_label = "🔥 Alto"
            elif tier == 2: tier_label = "⚖️ Medio"
            else: tier_label = "⚠️ Bajo"

            if posicion == 0: display_name = f"🥇 {brawler_name}"
            elif posicion == 1: display_name = f"🥈 {brawler_name}"
            elif posicion == 2: display_name = f"🥉 {brawler_name}"
            else: display_name = brawler_name
            
            personal_str = "-"
            if not personal_history.empty:
                stats = personal_history[personal_history['my_brawler'] == brawler_name]
                if len(stats) > 0:
                    wr_personal = int((stats['result'].sum()/len(stats))*100)
                    icon = "🔥" if wr_personal >= 60 else ("💀" if wr_personal <= 40 else "😐")
                    personal_str = f"{wr_personal}% {icon}"
            
            tabla_data.append({
                "Brawler": display_name,
                "Pop.": tier_label,
                "Puntuación": score, 
                "Tu WinRate": personal_str,
                "Picks": picks
            })
        
        df_tabla = pd.DataFrame(tabla_data)
        
        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Brawler": st.column_config.TextColumn("Brawler", width="medium"),
                "Pop.": st.column_config.TextColumn("Tier", width="small"),
                "Puntuación": st.column_config.ProgressColumn( 
                    "Puntuación",
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                "Tu WinRate": st.column_config.TextColumn("Tu Stats"),
                "Picks": st.column_config.NumberColumn("Veces Jugado", format="%d"),
            }
        )
    else:
        st.info("Selecciona un mapa para ver los datos.")

    if not aliados and not enemigos:
        st.caption("👈 Configura la partida en la izquierda para refinar el puntaje.")

    st.markdown("<br><div style='text-align: center;'><a href='#link_to_top' style='color: grey; text-decoration: none;'>⬆️ Volver Arriba</a></div>", unsafe_allow_html=True)