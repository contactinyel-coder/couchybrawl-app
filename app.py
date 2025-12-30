import streamlit as st
import pandas as pd
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- 1. DICCIONARIO DE TRADUCCIONES (TEXTOS UI) ---
TRANSLATIONS = {
    "Español": {
        "title": "🏆 BrawlSensei",
        "caption": "Tu asistente táctico para subir a Maestros",
        "sidebar_config": "⚙️ Configuración",
        "sidebar_profile": "👤 Tu Perfil",
        "db_global": "📚 Base de Datos Global",
        "map_label": "📍 Mapa:",
        "analyzed_matches": "📊 Partidas analizadas aquí:",
        "input_tag": "Player Tag (#...)",
        "btn_sync": "🔄 Sincronizar Historial",
        "btn_clear": "🗑️ Limpiar Todo",
        "your_matches": "☁️ Tus partidas:",
        "enemies": "### ⚔️ Enemigos",
        "enemies_label": "Ellos (Counters):",
        "allies": "### 🤝 Tu Equipo",
        "allies_label": "Tu aliado (Sinergia):",
        "recommendations": "### 🧠 Recomendaciones",
        "settings": "⚙️ Ajustes",
        "calibration": "**Calibración IA**",
        "calibration_help": "Partidas 'fantasma' añadidas. Mayor valor = Prioriza brawlers con muchas partidas.",
        "msg_short_tag": "❌ Tag demasiado corto",
        "msg_syncing": "Conectando con la nube de BrawlSensei...",
        "msg_success": "¡Historial cargado!",
        "msg_info_tag": "Ingresa tu Tag para ver tus estadísticas.",
        "msg_no_map": "Selecciona un mapa para ver los datos.",
        "col_brawler": "Brawler",
        "col_tier": "Pop.",
        "col_score": "Puntuación",
        "col_wr": "Tu WinRate",
        "col_picks": "Picks",
        "tier_meta": "💎 Meta",
        "tier_high": "🔥 Alto",
        "tier_mid": "⚖️ Medio",
        "tier_low": "⚠️ Bajo",
        "guide_title": "📖 Cómo usar BrawlSensei",
        "guide_text": """
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
        """
    },
    "English": {
        "title": "🏆 BrawlSensei",
        "caption": "Your tactical assistant to reach Masters",
        "sidebar_config": "⚙️ Configuration",
        "sidebar_profile": "👤 Your Profile",
        "db_global": "📚 Global Database",
        "map_label": "📍 Map:",
        "analyzed_matches": "📊 Matches analyzed here:",
        "input_tag": "Player Tag (#...)",
        "btn_sync": "🔄 Sync History",
        "btn_clear": "🗑️ Clear All",
        "your_matches": "☁️ Your Matches:",
        "enemies": "### ⚔️ Enemies",
        "enemies_label": "Them (Counters):",
        "allies": "### 🤝 Your Team",
        "allies_label": "Your Ally (Synergy):",
        "recommendations": "### 🧠 Recommendations",
        "settings": "⚙️ Settings",
        "calibration": "**AI Calibration**",
        "calibration_help": "Ghost matches added. Higher value = Prioritizes brawlers with more data.",
        "msg_short_tag": "❌ Tag is too short",
        "msg_syncing": "Connecting to BrawlSensei Cloud...",
        "msg_success": "History loaded!",
        "msg_info_tag": "Enter your Tag to see your stats.",
        "msg_no_map": "Select a map to see data.",
        "col_brawler": "Brawler",
        "col_tier": "Tier",
        "col_score": "Score",
        "col_wr": "Your WR",
        "col_picks": "Picks",
        "tier_meta": "💎 Meta",
        "tier_high": "🔥 High",
        "tier_mid": "⚖️ Mid",
        "tier_low": "⚠️ Low",
        "guide_title": "📖 How to use BrawlSensei",
        "guide_text": """
        **Quick Guide:**
        1. **📍 Map:** Select it.
        2. **⚔️ Draft:** Input enemy brawlers (find their counters) / input your allies (find their synergies).
        3. **🧠 Analysis:** Check the table sorted by Meta and Score.
        4. **🚫 Ban Phase:** The App has no "Ban" button, but use your brain: If the App says Piper and Nani are the best (highest score), **BAN THEM** if you don't have first pick, or leave them open if you pick first.
        
        **Legend:**
        * **💎 Meta:** Very popular Brawlers (Tier S).
        * **⚠️ Low:** Few data. Risky.
        * **🔥/💀 Your Performance:** Add your Player Tag and "sync history" to know your strengths and weaknesses.
        
        **⚠️ ATTENTION!** There is a game limit: it only records your last **25 played matches**! Be smart and sync your matches every time you play Ranked to build up your history data.
        """
    }
}

# --- 2. DICCIONARIO DE MAPAS (English -> Español) ---
MAP_NAME_TRANSLATIONS = {
    "Deathcap Trap": "Hiedra venenosa",
    "Dry Season": "Sequía sanguinaria",
    "Hideout": "Escondite",
    "Layer Cake": "Crimen organizado",
    "Shooting Star": "Tiroteo estelar",
    "Center Stage": "Palco central",
    "Grass Knot": "Campo de hierba",
    "Pinball Dreams": "Pinball",
    "Sneaky Fields": "Campos furtivos",
    "Spiraling Out": "Efecto envolvente",
    "Triple Dribble": "Triple drible",
    "Double Swoosh": "Brrrum brrrum",
    "Gem Fort": "Fuerte de gemas",
    "Hard Rock Mine": "Mina rocosa",
    "Undermine": "Cueva subterránea",
    "Bridge Too Far": "Aguas turbulentas",
    "Hot Potato": "Patata caliente",
    "Kaboom Canyon": "Cañón explosivo",
    "Safe Zone": "Refugio",
    "Dueling Beetles": "Duelo de escarabajos",
    "In the Liminal": "Al límite",
    "Open Business": "Campo abierto",
    "Parallel Plays": "Estrategias paralelas",
    "Ring of Fire": "Pista ardiente",
    "Belle's Rock": "Roca de Belle",
    "Flaring Phoenix": "Fénix en llamas",
    "Flowing Springs": "Manantial caudaloso",
    "Goldarm Gulch": "Barranco del brazo de oro",
    "New Horizons": "Nuevos horizontes",
    "Out in the Open": "A la intemperie"
}

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="BrawlSensei", layout="wide", initial_sidebar_state="expanded")

# ANCLA PARA IR ARRIBA
st.markdown("<div id='link_to_top'></div>", unsafe_allow_html=True)

# --- SELECTOR DE IDIOMA (BARRA LATERAL) ---
idioma_seleccionado = st.sidebar.selectbox("Language / Idioma", ["Español", "English"])
t = TRANSLATIONS[idioma_seleccionado] 

st.title(t["title"])
st.caption(t["caption"])

# ==========================================
# 🔑 ZONA DE CONFIGURACIÓN DE CLAVES
# ==========================================

API_KEY_LOCAL = "" 
try:
    API_KEY = st.secrets["BRAWL_API_KEY"]
except:
    API_KEY = API_KEY_LOCAL
if not API_KEY:
    API_KEY = "TOKEN_NO_CONFIGURADO"

HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://api.brawlstars.com/v1"

# --- CONFIGURACIÓN GOOGLE SHEETS ---
def conectar_google_sheets():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        except FileNotFoundError:
            st.error("❌ Error: secrets.json not found")
            st.stop()
    
    client = gspread.authorize(creds)
    sheet = client.open("Base_Datos_Brawl").sheet1
    return sheet

# --- LISTA DE MAPAS ---
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
    st.error("❌ Falta el archivo 'datos_ranked_raw.csv'.")
    st.stop()

# --- FUNCIONES AUXILIARES ---
def limpiar_seleccion():
    st.session_state['enemigos_key'] = []
    st.session_state['aliados_key'] = []

# --- 2. GESTIÓN CLOUD ---
def actualizar_historial_nube(player_tag):
    clean_tag = player_tag.replace("#", "").upper()
    try:
        hoja = conectar_google_sheets()
    except Exception as e:
        st.error(f"❌ Error Google Sheets: {e}")
        return pd.DataFrame()

    url = f"{BASE_URL}/players/%23{clean_tag}/battlelog"
    nuevos = []
    proxies = {}
    if "proxy" in st.secrets:
        proxies = {
            "http": st.secrets["proxy"]["server"],
            "https": st.secrets["proxy"]["server"]
        }

    try:
        response = requests.get(url, headers=HEADERS, timeout=10, proxies=proxies)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if not items:
                st.warning("⚠️ API OK, 0 items found.")

            for item in items:
                battle = item.get('battle', {})
                event = item.get('event', {})
                battle_time = item.get('battleTime')
                map_name = event.get('map') 
                
                if map_name not in MAPAS_RANKED:
                    continue 

                if 'event' in item and 'map' in item['event']:
                    result = battle.get('result', 'draw')
                    found_brawler = None
                    if 'teams' in battle:
                        for team in battle['teams']:
                            for p in team:
                                if p['tag'].replace("#", "").upper() == clean_tag:
                                    found_brawler = p['brawler']['name']
                                    break
                            if found_brawler: break
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
            st.error(f"❌ Tag invalid: #{clean_tag}")
            return pd.DataFrame()
        elif response.status_code == 403:
            st.error("❌ Error 403 (IP/Permission).")
            return pd.DataFrame()
        else:
            st.error(f"❌ Error API: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Connection Error: {e}")
        return pd.DataFrame()

    if nuevos:
        actuales = hoja.get_all_records()
        df_nube = pd.DataFrame(actuales)
        existentes = set()
        if not df_nube.empty:
            existentes = set(zip(df_nube['player_tag'].astype(str), df_nube['battle_time'].astype(str)))
        
        subir = [f for f in nuevos if (str(f[0]), str(f[1])) not in existentes]
        
        if subir:
            hoja.append_rows(subir)
            st.toast(f"☁️ +{len(subir)} Ranked matches saved.", icon="✅")
        else:
            st.toast("✅ No new matches.", icon="ℹ️")
    else:
        st.toast("✅ Synced (No new ranked matches).", icon="ℹ️")
            
    final = hoja.get_all_records()
    df_t = pd.DataFrame(final)
    if not df_t.empty: return df_t[df_t['player_tag'] == clean_tag]
    return pd.DataFrame()

# --- 3. BARRA LATERAL (LÓGICA DE MAPAS EN ESPAÑOL) ---
with st.sidebar:
    st.header(t["sidebar_config"])
    st.metric(label=t["db_global"], value=f"{len(df):,}")
    
    # --- LOGICA DE TRADUCCIÓN DE MAPAS ---
    # Función para mostrar el nombre correcto según el idioma
    def get_map_label(map_internal_name):
        if idioma_seleccionado == "Español":
            return MAP_NAME_TRANSLATIONS.get(map_internal_name, map_internal_name)
        return map_internal_name

    # Obtenemos mapas únicos (en inglés)
    unique_maps = df['map'].unique()
    
    # Ordenamos la lista basada en cómo se VERÁ (si es español, ordenamos por nombre español)
    sorted_maps = sorted(unique_maps, key=lambda x: get_map_label(x))
    
    # Creamos el selectbox usando format_func
    # Internamente 'mapa_seleccionado' tendrá el valor en INGLÉS (ej: "Bridge Too Far")
    # Pero el usuario verá "Aguas turbulentas"
    mapa_seleccionado = st.selectbox(
        t["map_label"], 
        sorted_maps, 
        format_func=get_map_label
    )
    
    if mapa_seleccionado:
        count_mapa = len(df[df['map'] == mapa_seleccionado])
        st.caption(f"{t['analyzed_matches']} **{count_mapa}**")
    
    st.divider()
    
    st.subheader(t["sidebar_profile"])
    user_tag = st.text_input(t["input_tag"], placeholder="#...")
    if st.button(t["btn_sync"]):
        if len(user_tag) < 3: st.error(t["msg_short_tag"])
        else:
            with st.spinner(t["msg_syncing"]):
                mis_datos = actualizar_historial_nube(user_tag)
                if not mis_datos.empty:
                    st.session_state['my_history'] = mis_datos
                    st.success(t["msg_success"])
    
    if 'my_history' in st.session_state and not st.session_state['my_history'].empty:
        hist = st.session_state['my_history']
        st.caption(f"{t['your_matches']} **{len(hist)}**")
        hist_sorted = hist.sort_values(by='battle_time', ascending=False)
        preview = hist_sorted.head(5).copy()[['map', 'my_brawler', 'result']]
        preview['result'] = preview['result'].apply(lambda x: "✅" if x == 1 else "❌")
        
        # Traducir nombre del mapa en la mini-tabla también
        if idioma_seleccionado == "Español":
            preview['map'] = preview['map'].apply(lambda x: MAP_NAME_TRANSLATIONS.get(x, x))
            
        preview.columns = ['Map', 'Brawler', 'Res']
        st.dataframe(preview, hide_index=True, use_container_width=True)
    else:
        st.info(t["msg_info_tag"])

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
        st.button(t["btn_clear"], on_click=limpiar_seleccion)

    col_enemigos, col_aliados = st.columns(2)
    with col_enemigos:
        st.markdown(t["enemies"])
        enemigos = st.multiselect(t["enemies_label"], sorted(df['my_brawler'].unique()), max_selections=3, key='enemigos_key')
    with col_aliados:
        st.markdown(t["allies"])
        aliados = st.multiselect(t["allies_label"], sorted(df['my_brawler'].unique()), max_selections=2, key='aliados_key')
    
    st.markdown("---")
    
    with st.expander(t["guide_title"], expanded=False):
        st.markdown(t["guide_text"])

# --- B. BLOQUE DERECHO ---
with bloque_der:
    col_titulo, col_ajustes = st.columns([4, 1])
    
    with col_titulo:
        st.markdown(t["recommendations"])
    
    with col_ajustes:
        with st.popover(t["settings"]):
            st.markdown(t["calibration"])
            C = st.slider(
                "C", 
                min_value=0, 
                max_value=200, 
                value=100, 
                step=10,
                help=t["calibration_help"]
            )

    if not meta_mapa.empty:
        recomendaciones = meta_mapa.copy()
        
        # 1. SCORE
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
        
        # 2. TIERS
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
        
        # 4. TABLA
        personal_history = st.session_state.get('my_history', pd.DataFrame())
        
        tabla_data = []
        
        for posicion, (index, row) in enumerate(top_picks.iterrows()):
            brawler_name = row['my_brawler']
            score = row['score_final']
            picks = row['partidas_mapa']
            tier = row['Tier']
            
            # Traducción dinámica de Tiers
            if tier == 4: tier_label = t["tier_meta"]
            elif tier == 3: tier_label = t["tier_high"]
            elif tier == 2: tier_label = t["tier_mid"]
            else: tier_label = t["tier_low"]

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
                t["col_brawler"]: display_name,
                t["col_tier"]: tier_label,
                t["col_score"]: score, 
                t["col_wr"]: personal_str,
                t["col_picks"]: picks
            })
        
        df_tabla = pd.DataFrame(tabla_data)
        
        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                t["col_brawler"]: st.column_config.TextColumn(t["col_brawler"], width="medium"),
                t["col_tier"]: st.column_config.TextColumn(t["col_tier"], width="small"),
                t["col_score"]: st.column_config.ProgressColumn( 
                    t["col_score"],
                    format="%.1f",
                    min_value=0,
                    max_value=100,
                ),
                t["col_wr"]: st.column_config.TextColumn(t["col_wr"]),
                t["col_picks"]: st.column_config.NumberColumn(t["col_picks"], format="%d"),
            }
        )
    else:
        st.info(t["msg_no_map"])

    st.markdown("<br><div style='text-align: center;'><a href='#link_to_top' style='color: grey; text-decoration: none;'>⬆️ Volver Arriba</a></div>", unsafe_allow_html=True)