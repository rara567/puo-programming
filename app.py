import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon
import math

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide")

# Custom CSS untuk mengikut gaya gambar (Dark Theme Sidebar & Custom Header)
st.markdown("""
    <style>
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
        color: white;
    }
    .st-emotion-cache-16ids0d {
        color: white;
    }
    
    /* Header Image/Banner Container */
    .header-box {
        background-color: #444;
        background-image: url('https://www.transparenttextures.com/patterns/cubes.png');
        padding: 30px;
        border-radius: 15px;
        text-align: left;
        color: white;
        margin-bottom: 20px;
        border-bottom: 5px solid #d35400;
        display: flex;
        align-items: center;
    }
    .header-logo {
        background-color: white;
        padding: 10px;
        border-radius: 50%;
        margin-right: 20px;
        width: 80px;
    }
    .header-text h1 {
        margin: 0;
        font-size: 40px;
        letter-spacing: 2px;
    }
    .header-text p {
        margin: 0;
        opacity: 0.8;
    }

    /* Profile Section */
    .profile-section {
        text-align: center;
        padding: 20px 0;
        background: linear-gradient(180deg, #0097b2 0%, #005f73 100%);
        border-radius: 0 0 20px 20px;
        margin-bottom: 20px;
    }
    .profile-pic {
        width: 80px;
        border-radius: 50%;
        border: 3px solid white;
    }
    </style>
    """, unsafe_allow_html=True)

# ================== LOGIK SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================== FUNGSI PEMPROSESAN ==================
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
    cols = st.columns([1, 1, 1])
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
    # ================== SIDEBAR (DASHBOARD MENU) ==================
    with st.sidebar:
        # Profile Section
        st.markdown("""
            <div class="profile-section">
                <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="profile-pic">
                <h3 style='color:white; margin-top:10px;'>Hai, Malfoy!</h3>
                <p style='color:white; opacity:0.8;'>Student</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.subheader("⚙️ Tetapan Paparan")
        
        # File Uploader di Sidebar
        uploaded_file = st.file_uploader("Upload fail CSV", type=["csv"])
        
        st.markdown("---")
        
        # Mod Peta Interaktif (FIX UNTUK SATELIT)
        st.subheader("🌍 Mod Peta Interaktif")
        sat_toggle = st.toggle("On/Off Peta Satelit", value=True)
        
        map_type = "Satalit (Hybrid)"
        if sat_toggle:
            map_type = st.radio("Pilih Jenis Peta:", ["Satalit (Hybrid)", "Satalit (Standard)"])
        else:
            st.info("Peta Standard (OpenStreetMap) sedang digunakan.")

        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390")

        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    # Header mengikut gambar
    st.markdown("""
        <div class="header-box">
            <div class="header-logo">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Logo_Politeknik_Malaysia.png/800px-Logo_Politeknik_Malaysia.png" width="60">
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
                    # Kira Luas
                    coords = list(zip(df['E'], df['N']))
                    poly = Polygon(coords)
                    area = poly.area
                    
                    # Paparan Peta
                    center_lat = df_mapped['lat'].mean()
                    center_lon = df_mapped['lon'].mean()
                    
                    # Inisialisasi Peta
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=19)

                    # LOGIK LAYER SATELIT (FIXED)
                    if sat_toggle:
                        if map_type == "Satalit (Hybrid)":
                            tile_url = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}' # Hybrid
                        else:
                            tile_url = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}' # Satellite only
                        
                        folium.TileLayer(
                            tiles=tile_url,
                            attr='Google',
                            name='Google Satellite',
                            overlay=False,
                            control=True
                        ).add_to(m)
                    
                    # Lukis Sempadan
                    locations = df_mapped[['lat', 'lon']].values.tolist()
                    # Menutup polygon
                    if locations[0] != locations[-1]:
                        locations.append(locations[0])
                    
                    folium.Polygon(
                        locations, 
                        color="yellow", 
                        weight=3, 
                        fill=True, 
                        fill_opacity=0.2
                    ).add_to(m)

                    # Tambah Label Luas di tengah
                    folium.Marker(
                        [center_lat, center_lon],
                        icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: #2ecc71; font-weight: bold; font-size: 15pt;">{area:.2f} m²</div>""")
                    ).add_to(m)
                    
                    # Titik Stesen dengan Nombor
                    for _, row in df_mapped.iterrows():
                        folium.CircleMarker(
                            [row['lat'], row['lon']], 
                            radius=5, color="red", fill=True, fill_color="white"
                        ).add_to(m)
                        
                        folium.Marker(
                            [row['lat'], row['lon']],
                            icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: white; background: red; border-radius: 50%; width: 20px; height: 20px; text-align: center; font-size: 10pt; font-weight: bold; border: 1px solid white;">{int(row['STN'])}</div>""")
                        ).add_to(m)

                    folium_static(m, width=1000, height=500)
                    
                    # Jadual Data di bawah
                    st.markdown("### 📊 Data Koordinat")
                    st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)

            else:
                st.error("Fail CSV mesti mempunyai kolum: STN, E, N")
        except Exception as e:
            st.error(f"Ralat pemprosesan: {e}")
    else:
        st.info("Sila muat naik fail CSV di sidebar untuk melihat visualisasi lot.")
