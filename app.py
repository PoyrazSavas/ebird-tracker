import streamlit as st
import os
import random
import time
import datetime
from dotenv import load_dotenv
from ebird_client import EBirdClient
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="eBird Tracker", page_icon="🦉", layout="wide", initial_sidebar_state="collapsed")

# --- SESSION STATE ---
if 'lang' not in st.session_state: st.session_state.lang = 'en'
if 'theme' not in st.session_state: st.session_state.theme = 'dark'
if 'region_species' not in st.session_state: st.session_state.region_species = {}
if 'search_active' not in st.session_state: st.session_state.search_active = False
if 'current_data' not in st.session_state: st.session_state.current_data = None
if 'current_loc_title' not in st.session_state: st.session_state.current_loc_title = ""
if 'first_visit' not in st.session_state: st.session_state.first_visit = True
if 'show_help' not in st.session_state: st.session_state.show_help = False
if 'botd' not in st.session_state: st.session_state.botd = None  # Bird of the Day cache
if 'loaded' not in st.session_state: st.session_state.loaded = False # Splash screen flag

def toggle_lang(): st.session_state.lang = 'tr' if st.session_state.lang == 'en' else 'en'
def toggle_theme(): st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'

# --- TRANSLATIONS ---
texts = {
    'en': {
        'title': 'eBird Tracker',
        'tribute': "With love from Galatasaray High School Birdwatching Club",
        'tab_h': '📍 Location', 'load_species': 'Load Species',
        'h_sp': 'Select Bird Species', 'btn_scan': 'Explore Observations',
        'spinner': '🌲 Exploring...', 'no_records': 'No records found.',
        'view': 'View ↗', 'map_title': 'Interactive Map',
        'botd_title': 'BIRD OF THE DAY',
        'botd_tag': '🇹🇷 Turkey — Resident Species',
        'botd_regional_tag': '📍 Spotted in Selected Region',
        'botd_start': '👈 Select a location and species to explore the map.',
        'botd_loading': '🔍 Finding today\'s bird...',
        'botd_wiki': 'Read on Wikipedia ↗',
    },
    'tr': {
        'title': 'eBird Tracker',
        'tribute': "Galatasaray Lisesi Kuş Gözlem Kulübü'nden sevgilerle",
        'tab_h': '📍 Lokasyon', 'load_species': 'Türleri Listele',
        'h_sp': 'Kuş Türü Seçin', 'btn_scan': 'Gözlemleri Keşfet',
        'spinner': '🌲 Yükleniyor...', 'no_records': 'Kayıt bulunamadı.',
        'view': 'Gör ↗', 'map_title': 'İnteraktif Harita',
        'botd_title': 'GÜNÜN KUŞU',
        'botd_tag': '🇹🇷 Türkiye — Yerleşik Tür',
        'botd_regional_tag': '📍 Seçilen Bölgede Gözlemlendi',
        'botd_start': '👈 Haritayı görmek için konum ve tür seçin.',
        'botd_loading': '🔍 Günün kuşu aranıyor...',
        'botd_wiki': 'Wikipedia\'da Oku ↗',
    }
}
t = texts[st.session_state.lang]

# --- THEME CONFIG ---
if st.session_state.theme == 'light':
    EBIRD_GREEN = "#10B981" # Canlı İlkbahar Yeşili
    bg, card_bg, text_p, text_s, border = "#F8FAFC", "#FFFFFF", "#0F172A", "#64748B", "#E2E8F0"
    shadow = "rgba(148, 163, 184, 0.12)"
    map_tile = "CartoDB positron"
else:
    EBIRD_GREEN = "#A3E635" # Fosforlu Gece Yeşili
    bg, card_bg, text_p, text_s, border = "#0B1120", "#1E293B", "#F1F5F9", "#94A3B8", "#334155"
    shadow = "rgba(0, 0, 0, 0.25)"
    map_tile = "CartoDB dark_matter"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Quicksand:wght@400;500;600&display=swap');
    
    #MainMenu, header, footer, [data-testid="stSidebar"] {{display: none !important;}}
    .stApp {{
        background-color: {bg}; 
        transition: background-color 0.4s ease;
    }}
    
    /* Genel Tipografi - Daha güvenli seçiciler */
    * {{ font-family: 'Quicksand', sans-serif !important; }}
    body, p, div, span {{ color: {text_p}; }}
    
    /* Başlıklar */
    h1, h2, h3, h4, .st-metric-label, .app-title, .species-name, [data-testid="stHeader"] {{
        font-family: 'Lora', serif !important;
    }}
    
    .app-title {{
        color: {EBIRD_GREEN} !important; 
        font-weight: 800; 
        font-size: 3.2rem; 
        text-align: center; 
        margin-bottom: 1.5rem;
        letter-spacing: -0.03em;
        text-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }}
    
    /* Canlı Kart Tasarımı */
    .ebird-card {{
        background-color: {card_bg}; 
        border-radius: 20px; 
        padding: 20px; 
        margin-bottom: 20px; 
        border: 1px solid {border}; 
        box-shadow: 0 10px 25px -5px {shadow};
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    .ebird-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 20px 30px -10px {shadow};
        border-color: {EBIRD_GREEN}55;
    }}
    
    .species-name {{
        color: {EBIRD_GREEN} !important; 
        font-weight: 700; 
        font-size: 1.3rem;
    }}
    
    /* Buton Modernizasyonu */
    .stButton>button {{
        border-radius: 12px !important; 
        font-weight: 700 !important;
        background-color: {EBIRD_GREEN} !important;
        color: {bg} !important;
        border: none !important;
        padding: 0.6rem 1.5rem !important;
        width: 100%;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px {EBIRD_GREEN}44 !important;
        margin-bottom: 10px;
    }}
    
    .stButton>button:hover {{
        transform: scale(1.02);
        box-shadow: 0 6px 20px {EBIRD_GREEN}66 !important;
    }}
    
    /* Input ve Selectbox Stabilizasyonu */
    .stTextInput, .stSelectbox {{
        margin-bottom: 20px !important;
    }}
    
    .stTextInput>div>div>input, .stSelectbox>div {{
        border-radius: 12px !important;
        background-color: {card_bg} !important;
        border: 2px solid {border} !important;
        transition: all 0.3s ease !important;
    }}
    
    .stTextInput>div>div>input:focus, .stSelectbox>div:focus-within {{
        border-color: {EBIRD_GREEN} !important;
        box-shadow: 0 0 0 4px {EBIRD_GREEN}22 !important;
        outline: none !important;
    }}

    /* Dropdown Menü (BaseWeb) Düzeltmesi */
    div[data-baseweb="select"] {{
        background-color: transparent !important;
    }}
    
    .tribute-footer {{
        position: fixed; bottom: 15px; right: 20px; 
        color: {text_s}; opacity: 0.6; 
        font-size: 0.85rem; font-style: italic;
    }}
    
    iframe {{border-radius: 20px; border: 1px solid {border};}}
    
    /* Loader Animasyonları */
    @keyframes pulse {{
        0% {{ transform: scale(0.95); opacity: 0.5; }}
        50% {{ transform: scale(1.05); opacity: 1; }}
        100% {{ transform: scale(0.95); opacity: 0.5; }}
    }}
    .loader-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: {bg}; display: flex; flex-direction: column;
        align-items: center; justify-content: center; z-index: 99999;
        pointer-events: none;
    }}
    .loader-bird {{ font-size: 5rem; animation: pulse 1.5s infinite ease-in-out; }}
    .loader-text {{ 
        font-family: 'Lora', serif; font-size: 1.2rem; color: {EBIRD_GREEN}; 
        margin-top: 20px; letter-spacing: 0.1rem; opacity: 0.8;
    }}
    </style>
    <div class="tribute-footer">{t['tribute']}</div>
    """, unsafe_allow_html=True)

# --- STATIC TURKISH BIRD POOL ---
TURKEY_BIRDS = [
    {"com": "White Stork",          "sci": "Ciconia ciconia",         "tr_name": "Leylek"},
    {"com": "Mallard",              "sci": "Anas platyrhynchos",      "tr_name": "Yeşilbaş"},
    {"com": "Common Blackbird",     "sci": "Turdus merula",           "tr_name": "Karatavuk"},
    {"com": "Eurasian Jay",         "sci": "Garrulus glandarius",     "tr_name": "Alakarga"},
    {"com": "House Sparrow",        "sci": "Passer domesticus",       "tr_name": "Serçe"},
    {"com": "Barn Swallow",         "sci": "Hirundo rustica",         "tr_name": "Kırlangıç"},
    {"com": "European Goldfinch",   "sci": "Carduelis carduelis",     "tr_name": "Saka"},
    {"com": "Common Swift",         "sci": "Apus apus",               "tr_name": "Siyah Sağan"},
    {"com": "Little Egret",         "sci": "Egretta garzetta",        "tr_name": "Küçük Ak Balıkçıl"},
    {"com": "Eurasian Hoopoe",      "sci": "Upupa epops",             "tr_name": "Çavuşkuşu"},
]

# --- WIKIPEDIA API ---
@st.cache_data(ttl="1d")
def get_wiki_data(sci_name: str, com_name: str) -> dict:
    result = {"img_url": None, "summary": "", "wiki_url": ""}
    headers = {"User-Agent": "eBirdTracker/1.0 (educational project)"}

    def try_rest(title: str) -> bool:
        try:
            slug = title.strip().replace(" ", "_")
            resp = requests.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}",
                timeout=7, headers=headers)
            if resp.status_code != 200:
                return False
            data = resp.json()
            thumb = data.get("originalimage") or data.get("thumbnail")
            img   = thumb.get("source") if thumb else None
            summ  = data.get("extract", "")
            wurl  = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            if summ:
                result["img_url"]  = img
                result["summary"]  = summ[:300] + ("..." if len(summ) > 300 else "")
                result["wiki_url"] = wurl
                return True
        except Exception:
            pass
        return False

    if try_rest(sci_name): return result
    if try_rest(com_name): return result
    
    try:
        r = requests.get("https://en.wikipedia.org/w/api.php",
                         params={"action": "query", "list": "search",
                                 "srsearch": com_name, "format": "json", "srlimit": 3},
                         timeout=6, headers=headers)
        for hit in r.json().get("query", {}).get("search", []):
            if try_rest(hit["title"]): return result
    except Exception: pass
    return result

# --- SEEDED SELECTION HELPER ---
def select_daily_bird(bird_pool, loc_id="WORLD"):
    today = str(datetime.date.today())
    seed_val = f"{today}_{loc_id}"
    rng = random.Random(seed_val)
    if isinstance(bird_pool, list):
        return rng.choice(bird_pool)
    elif isinstance(bird_pool, dict):
        keys = sorted(list(bird_pool.keys()))
        if not keys: return None
        picked_name = rng.choice(keys)
        info = bird_pool[picked_name]
        return {"com": picked_name, "sci": info.get("sciName", picked_name), "tr_name": picked_name}
    return None

# --- BIRD OF THE DAY RENDERER ---
def render_bird_of_day(bird: dict, is_regional: bool = False):
    if not bird: return
    com_name     = bird.get("com", "")
    sci_name     = bird.get("sci", "")
    tr_name      = bird.get("tr_name", com_name)
    display_name = tr_name if st.session_state.lang == 'tr' else com_name

    wiki     = bird.get("wiki") or {}
    img_url  = wiki.get("img_url")
    summary  = (wiki.get("summary", "") or "—").replace('"', '&quot;')
    wiki_url = wiki.get("wiki_url", "")
    tag      = t['botd_regional_tag'] if is_regional else t['botd_tag']

    with st.container():
        if img_url and str(img_url).startswith("http"):
            try:
                st.image(img_url, use_container_width=True)
            except Exception:
                st.markdown(f'<div style="width:100%; height:150px; display:flex; align-items:center; justify-content:center; font-size:4rem; background:linear-gradient(135deg,#1a2e0a,#2d4a15); border-radius:12px 12px 0 0;">🦅</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="width:100%; height:150px; display:flex; align-items:center; justify-content:center; font-size:4rem; background:linear-gradient(135deg,#1a2e0a,#2d4a15); border-radius:12px 12px 0 0;">🦅</div>', unsafe_allow_html=True)

        wiki_btn = f'<a href="{wiki_url}" target="_blank" style="display:inline-block; margin-top:12px; padding:6px 15px; background:{EBIRD_GREEN}; color:white; border-radius:8px; text-decoration:none; font-size:0.75rem; font-weight:600; box-shadow:0 2px 5px rgba(90,139,34,0.3);">{t["botd_wiki"]}</a>' if wiki_url else ""
        
        st.markdown(f"""
        <div style="background:{card_bg}; padding:15px 18px 15px; border:1px solid {border}; border-top:none; border-radius:0 0 16px 16px; margin-top:-10px; box-shadow:0 4px 15px rgba(0,0,0,0.1); margin-bottom:15px;">
            <div style="font-size:0.65rem; font-weight:700; letter-spacing:0.1em; color:{EBIRD_GREEN}; margin-bottom:6px; text-transform:uppercase;">✦ {t['botd_title']}</div>
            <div style="font-size:1.4rem; font-weight:800; line-height:1.1; margin-bottom:3px; font-family:'Lora', serif;">{display_name}</div>
            <div style="font-size:0.8rem; font-style:italic; opacity:0.6; margin-bottom:10px;">{sci_name}</div>
            <div style="display:inline-block; background:{EBIRD_GREEN}15; border:1px solid {EBIRD_GREEN}33; border-radius:15px; padding:2px 10px; font-size:0.7rem; margin-bottom:10px;">{tag}</div>
            <div style="font-size:0.8rem; line-height:1.5; opacity:0.8;">{summary}</div>
            {wiki_btn}
        </div>
        """, unsafe_allow_html=True)

# --- HELPERS ---
def get_observer_name(obs, lang):
    name = obs.get("userDisplayName") if isinstance(obs, dict) else None
    if name and isinstance(name, str) and name.strip():
        return name
    if obs.get("locationPrivate") if isinstance(obs, dict) else False:
        return "Gizli" if lang == 'tr' else "Private"
    return "Anonim" if lang == 'tr' else "Anonymous"

def render_obs_card(obs, species_name):
    obs_name = get_observer_name(obs, st.session_state.lang)
    count = obs.get('howMany', 'X')
    sub_id = obs.get('subId', '')
    loc_name = obs.get('locName', '')
    obs_dt = obs.get('obsDt', '')
    st.markdown(f"""
    <div class="ebird-card" style="padding:18px 20px;">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:10px;">
            <div>
                <div class="species-name" style="font-size:1.1rem; margin-bottom:6px;">🦉 {species_name}</div>
                <div style="display:flex; flex-wrap:wrap; gap:8px; font-size:0.82rem; margin-bottom:8px;">
                    <span style="background:{EBIRD_GREEN}22;padding:2px 8px;border-radius:12px;">👤 {obs_name}</span>
                    <span style="background:{EBIRD_GREEN}22;padding:2px 8px;border-radius:12px;">📅 {obs_dt}</span>
                    <span style="background:{EBIRD_GREEN}22;padding:2px 8px;border-radius:12px;">🔢 {count}</span>
                </div>
                <div style="font-size:0.8rem;opacity:0.7;">📍 {loc_name}</div>
            </div>
            <a href="https://ebird.org/checklist/{sub_id}" target="_blank"
               style="background:{EBIRD_GREEN};color:white;padding:8px 16px;border-radius:8px;
                      text-decoration:none;font-size:0.8rem;font-weight:700;white-space:nowrap;
                      box-shadow:0 2px 6px rgba(90,139,34,0.35);flex-shrink:0;">
                {t['view']}
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)

@st.dialog("eBird Tracker Guide 🦉")
def welcome_dialog():
    is_tr = st.session_state.lang == 'tr'
    title    = "eBird Tracker'a Hoş Geldiniz" if is_tr else "Welcome to eBird Tracker"
    subtitle = "Bölgenizdeki gözlemleri saniyeler içinde haritada takip edin." if is_tr else "Explore bird sightings in any region on an interactive map."
    btn_label = "Hadi Başlayalım →" if is_tr else "Let's Start →"
    steps_tr = [
        ("📍", "Lokasyon Gir",     "Hotspot ID (örn: L123456) veya Bölge Kodu (örn: TR-34) yazın."),
        ("🦉", "Tür Yükle",       "'Türleri Listele'ye basın — bölgedeki kuşlar anında listelenir."),
        ("🗺️", "Haritada Keşfet", "Bir kuş seçin, gözlemleri interaktif harita üzerinde görün."),
    ]
    steps_en = [
        ("📍", "Enter Location",  "Type a Hotspot ID (e.g. L123456) or Region Code (e.g. TR-34)."),
        ("🦉", "Load Species",    "Click 'Load Species' — birds recently seen in that area appear."),
        ("🗺️", "Explore the Map", "Select a species and view its sightings on the interactive map."),
    ]
    steps = steps_tr if is_tr else steps_en
    st.markdown(f"""
        <div style="text-align:center; padding:0 0 15px;">
            <div style="font-size:1.4rem; font-weight:800; color:#5a8b22; margin-bottom:4px;">{title}</div>
            <div style="font-size:0.85rem; opacity:0.65;">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)
    for i, (icon, step_title, step_desc) in enumerate(steps):
        st.markdown(f"""
            <div style="display:flex;align-items:flex-start;gap:12px;background:#5a8b2209;
                        border:1px solid #5a8b2228;border-radius:10px;padding:12px 14px;margin-bottom:8px;">
                <div style="font-size:1.4rem;line-height:1;flex-shrink:0;">{icon}</div>
                <div>
                    <div style="font-weight:700;color:#5a8b22;font-size:0.85rem;margin-bottom:2px;">{i+1}. {step_title}</div>
                    <div style="font-size:0.75rem;opacity:0.75;line-height:1.4;">{step_desc}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    st.markdown("<div style='margin-top:5px'></div>", unsafe_allow_html=True)
    if st.button(btn_label, type="primary", use_container_width=True):
        st.session_state.first_visit = False
        st.rerun()

# --- MAIN ---
def main():
    if not st.session_state.get('loaded', False):
        placeholder = st.empty()
        with placeholder.container():
            st.markdown(f"""
                <div class="loader-container" style="pointer-events: auto;">
                    <div class="loader-bird">🦉</div>
                    <div class="loader-text">{t['spinner']}</div>
                </div>
            """, unsafe_allow_html=True)
            time.sleep(2.2)
        placeholder.empty()
        st.session_state.loaded = True

    try:
        api_key = st.secrets["EBIRD_API_KEY"]
    except Exception:
        api_key = os.getenv("EBIRD_API_KEY", "")
    
    client  = EBirdClient(api_key)

    if st.session_state.botd is None:
        bird = select_daily_bird(TURKEY_BIRDS, "TURKEY").copy()
        with st.spinner(t['botd_loading']):
            bird["wiki"] = get_wiki_data(bird["sci"], bird["com"])
        st.session_state.botd = {"bird": bird, "is_regional": False}

    st.markdown(f'<div class="app-title">🦉 {t["title"]}</div>', unsafe_allow_html=True)
    
    if st.session_state.first_visit or st.session_state.show_help:
        st.session_state.first_visit = False
        st.session_state.show_help = False
        welcome_dialog()
    c1, c2, c3, c4 = st.columns([10, 1, 1, 1])
    with c2:
        if st.button("🇹🇷" if st.session_state.lang == 'en' else "🇬🇧"): toggle_lang(); st.rerun()
    with c3:
        if st.button("☀️" if st.session_state.theme == 'dark' else "🌙"): toggle_theme(); st.rerun()
    with c4:
        if st.button("❓", help="How to use / Nasıl Kullanılır?"):
            st.toast("Opening guide... 📖" if st.session_state.lang == 'en' else "Kılavuz açılıyor... 📖")
            st.session_state.show_help = True
            st.rerun()

    col_input, col_display = st.columns([1, 2])

    with col_input:
        st.markdown(f"#### 🔎 {t['tab_h']}")
        loc_id = st.text_input("", placeholder="TR-34, L123...", key="loc_input", label_visibility="collapsed")

        if st.button(t['load_species'], use_container_width=True):
            if not loc_id:
                st.warning("Lütfen bir lokasyon girin!" if st.session_state.lang == 'tr' else "Please enter a location!")
            else:
                st.session_state.search_active = False
                with st.spinner(t['spinner']):
                    try:
                        st.session_state.region_species = client.get_recent_species_in_region(loc_id)
                        if not st.session_state.region_species:
                            st.info("Bu bölgede son 30 günde gözlem bulunamadı." if st.session_state.lang == 'tr' else "No observations found in this region for the last 30 days.")
                        
                        # Bölgesel Bird of the Day
                        if st.session_state.region_species:
                            new_bird = select_daily_bird(st.session_state.region_species, loc_id)
                            if new_bird:
                                new_bird["wiki"] = get_wiki_data(new_bird["sci"], new_bird["com"])
                                st.session_state.botd = {"bird": new_bird, "is_regional": True}
                    except Exception as e:
                        st.error(f"⚠️ API Bağlantı Hatası: {str(e)}")

        st.divider()
        st.markdown(f"#### 🦉 {t['h_sp']}")
        options = sorted(list(st.session_state.region_species.keys()))
        selected_bird = st.selectbox("", options=[""] + options, index=0, key="sp_select", label_visibility="collapsed")

        if selected_bird and selected_bird != "":
            with st.spinner(t['spinner']):
                sp_info = st.session_state.region_species[selected_bird]
                if loc_id.startswith("L"):
                    st.session_state.current_data = client.get_hotspot_observations(loc_id, sp_info['code'])
                    st.session_state.current_loc_title = client.get_hotspot_name(loc_id)
                else:
                    st.session_state.current_data = client.get_region_observations(loc_id, sp_info['code'])
                    st.session_state.current_loc_title = loc_id
                st.session_state.search_active = True
                st.session_state.last_selected_bird = selected_bird

    with col_display:
        if st.session_state.search_active and st.session_state.current_data:
            data = st.session_state.current_data
            df   = pd.DataFrame(data)

            m = folium.Map(location=[df['lat'].mean(), df['lng'].mean()], zoom_start=10, tiles=map_tile)
            obs_label   = "Gözlemci" if st.session_state.lang == 'tr' else "Observer"
            date_label  = "Tarih"    if st.session_state.lang == 'tr' else "Date"
            count_label = "Sayı"     if st.session_state.lang == 'tr' else "Count"
            bird_label  = st.session_state.last_selected_bird

            for _, row in df.iterrows():
                raw_name   = row.get('userDisplayName')
                is_private = bool(row.get('locationPrivate', False))
                anon       = 'Anonim' if st.session_state.lang == 'tr' else 'Anonymous'
                priv_lbl   = 'Gizli'  if st.session_state.lang == 'tr' else 'Private'
                if raw_name and isinstance(raw_name, str) and raw_name.strip():
                    name = raw_name
                elif is_private:
                    name = f"🔒 {priv_lbl}"
                else:
                    name = anon
                count  = row.get('howMany', 'X')
                sub_id = row.get('subId', '')
                popup_html = f"""
                <div style="font-family:Arial,sans-serif;min-width:230px;padding:4px;">
                    <div style="font-size:15px;font-weight:800;color:{EBIRD_GREEN};
                                border-bottom:2px solid {EBIRD_GREEN}33;padding-bottom:6px;margin-bottom:8px;">
                        🦉 {bird_label}
                    </div>
                    <table style="font-size:13px;color:#2d3748;line-height:1.8;width:100%;">
                        <tr><td><b>👤 {obs_label}</b></td><td>{name}</td></tr>
                        <tr><td><b>📅 {date_label}</b></td><td>{row['obsDt']}</td></tr>
                        <tr><td><b>🔢 {count_label}</b></td><td>{count}</td></tr>
                    </table>
                    <div style="margin-top:10px;text-align:right;">
                        <a href="https://ebird.org/checklist/{sub_id}" target="_blank"
                           style="background:{EBIRD_GREEN};color:white;padding:7px 16px;
                                  border-radius:7px;text-decoration:none;font-size:12px;font-weight:bold;">
                            {t['view']}
                        </a>
                    </div>
                </div>"""
                iframe = folium.IFrame(html=popup_html, width=260, height=170)
                folium.Marker([row['lat'], row['lng']],
                              popup=folium.Popup(iframe, max_width=260),
                              icon=folium.Icon(color='green', icon='dove', prefix='fa')).add_to(m)

            st.markdown(f"##### 🗺️ {t['map_title']}: {st.session_state.current_loc_title}")
            st_folium(m, width="100%", height=400, key="map_stable")
            st.divider()
            for obs in data[:10]:
                render_obs_card(obs, st.session_state.last_selected_bird)

        else:
            # --- BIRD OF THE DAY ---
            botd_data = st.session_state.botd
            if botd_data:
                render_bird_of_day(botd_data["bird"], botd_data["is_regional"])
            else:
                st.info(t['botd_start'])

if __name__ == "__main__": main()
