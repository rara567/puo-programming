import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon
import base64
import os

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide", page_icon="📍")

# Gantikan dengan URL Raw GitHub anda yang betul
# Jika fail puo.png ada dalam folder yang sama di GitHub, guna nama fail sahaja
LOGO_PATH = "puo.png" 
GITHUB_RAW_URL = "https://raw.githubusercontent.com/username_anda/repo_anda/main/puo.png"

# Fungsi untuk menukar imej tempatan ke Base64 (untuk paparan dalam HTML)
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

img_base64 = get_base64_image(LOGO_PATH)

# Custom CSS
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{
        background-color: #1E1E1E;
        color: white;
    }}
    .header-box {{
        background-color: #444;
        background-image: url('https://www.transparenttextures.com/patterns/cubes.png');
        padding: 30px;
        border-radius: 15px;
        display: flex;
        align-items: center;
        color: white;
        margin-bottom: 20px;
        border-bottom: 5px solid #d35400;
    }}
    .header-logo-container {{
        background-color: white;
        padding: 5px;
        border-radius: 50%;
        margin-right: 20px;
        width: 100px;
        height: 100px;
        display: flex;
        justify-content: center;
        align-items: center;
        overflow: hidden;
    }}
    .header-logo-container img {{
        max-width: 90%;
        max-height: 90%;
    }}
    .header-text h1 {{
        margin: 0;
        font-size: 40px;
        letter-spacing: 2px;
    }}
    .profile-section {{
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(180deg, #0097b2 0%, #005f73 100%);
        border-radius: 15px;
        margin-bottom: 20px;
    }}
    .profile-pic {{
        width: 80px;
        border-radius: 50%;
        border: 3px solid white;
    }}
    </style>
    """, unsafe_allow_html=True)

# ================== LOGIK SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def transform_coords(df, from_epsg):
    try:
        transformer = Transformer.from_crs(f"EPSG:{from_epsg}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        df['lat'] = lat
        df['lon'] = lon
        return df
    except Exception as e:
        st.error(f"Ralat EPSG: {e}")
        return None

# ================== HALAMAN LOGIN ==================
if not st.session_state.logged_in:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.write("# 🔐 Login")
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type="password")
        if st.button("Log Masuk", use_container_width=True):
            if user_id == "67" and password == "ikmalkacak":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("ID atau Kata Laluan Salah")
else:
    # ================== SIDEBAR ==================
    with st.sidebar:
        st.markdown("""
            <div class="profile-section">
                <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="profile-pic">
                <h3 style='color:white; margin-top:10px;'>Hai, Hzzrull!</h3>
                <p style='color:white; opacity:0.8;'>Student</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Paparan Logo di Sidebar (Guna st.image lebih selamat)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
        else:
            st.image(GITHUB_RAW_URL, width=150)
            
        st.subheader("⚙️ Tetapan Paparan")
        uploaded_file = st.file_uploader("Upload fail CSV", type=["csv"])
        
        st.markdown("---")
        st.subheader("🌍 Mod Peta Interaktif")
        sat_toggle = st.toggle("On/Off Peta Satelit", value=True)
        
        if sat_toggle:
            map_type = st.radio("Pilih Jenis Peta:", ["Satalit (Hybrid)", "Satalit (Standard)"])
        
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390")

        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    # Banner Header dengan pembetulan Logo
    logo_html = ""
    if img_base64:
        logo_html = f'<img src="data:image/png;base64,{img_base64}">'
    else:
        logo_html = f'<img src="{GITHUB_RAW_URL}">'

    st.markdown(f"""
        <div class="header-box">
            <div class="header-logo-container">
                {logo_html}
            </div>
            <div class="header-text">
                <h1>RUMAH</h1>
                <p>Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            
            if all(x in df.columns for x in ['E', 'N', 'STN']):
                df_mapped = transform_coords(df.copy(), epsg_code)
                
                if df_mapped is not None:
                    coords = list(zip(df['E'], df['N']))
                    poly = Polygon(coords)
                    area = poly.area
                    
                    center_lat = df_mapped['lat'].mean()
                    center_lon = df_mapped['lon'].mean()
                    
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=19)

                    if sat_toggle:
                        tile_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' if map_type == "Satalit (Hybrid)" else 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}'
                        folium.TileLayer(tiles=tile_url, attr='Google', name='Google Satellite', overlay=False).add_to(m)
                    
                    locations = df_mapped[['lat', 'lon']].values.tolist()
                    if locations[0] != locations[-1]: locations.append(locations[0])
                    
                    folium.Polygon(locations, color="yellow", weight=3, fill=True, fill_opacity=0.2).add_to(m)

                    folium.Marker(
                        [center_lat, center_lon],
                        icon=folium.DivIcon(html=f'<div style="color: #2ecc71; font-weight: bold; font-size: 15pt; text-shadow: 1px 1px black;">{area:.2f} m²</div>')
                    ).add_to(m)
                    
                    for _, row in df_mapped.iterrows():
                        folium.CircleMarker([row['lat'], row['lon']], radius=5, color="red", fill=True, fill_color="white").add_to(m)
                        folium.Marker(
                            [row['lat'], row['lon']],
                            icon=folium.DivIcon(html=f'<div style="color: white; background: red; border-radius: 50%; width: 22px; height: 22px; text-align: center; font-size: 9pt; font-weight: bold; border: 2px solid white;">{int(row["STN"])}</div>')
                        ).add_to(m)

                    folium_static(m, width=1100, height=500)
                    st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
        except Exception as e:
            st.error(f"Ralat: {e}")
    else:
        st.info("Sila muat naik fail CSV di sidebar.")
