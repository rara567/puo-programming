import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon, mapping
import json
import base64
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MatplotlibPolygon

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide", page_icon="📍")

# Path Fail Lokal (Pastikan fail-fail ini ada di folder yang sama)
LOGO_PATH = "puo.png" 
VIDEO_PATH = "video.mp4" 

# Fungsi-fungsi Utiliti
def get_base64_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def format_bearing(degrees):
    """Menukar darjah perpuluhan kepada format D°M'S\"."""
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = int((degrees - d - m/60) * 3600)
    return f"{abs(d)}°{abs(m)}'{abs(s)}\""

def calculate_bearing_distance(p1, p2):
    """Mengira bearing (dari Utara) dan jarak antara dua titik koordinat local (E, N)."""
    de = p2[0] - p1[0]
    dn = p2[1] - p1[1]
    
    # Jarak (Pythagoras)
    distance = math.sqrt(de**2 + dn**2)
    
    # Bearing (dari Utara)
    angle_rad = math.atan2(de, dn)
    bearing_deg = math.degrees(angle_rad)
    
    if bearing_deg < 0:
        bearing_deg += 360
        
    return format_bearing(bearing_deg), distance

# Muat data base64
img_base64 = get_base64_file(LOGO_PATH)
vid_base64 = get_base64_file(VIDEO_PATH)

# ================== CUSTOM CSS ==================
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: #1E1E1E; color: white; }}
    
    /* Header Video Style */
    .header-container {{
        position: relative;
        width: 100%;
        height: 200px;
        overflow: hidden;
        border-radius: 15px;
        margin-bottom: 20px;
        border-bottom: 5px solid #d35400;
        display: flex;
        align-items: center;
        background-color: black;
    }}
    #video-bg {{
        position: absolute;
        top: 50%; left: 50%;
        min-width: 100%; min-height: 100%;
        width: auto; height: auto;
        z-index: 0;
        transform: translate(-50%, -50%);
        object-fit: cover;
        pointer-events: none;
    }}
    .header-overlay {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.4);
        z-index: 1;
    }}
    .header-content {{
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        padding-left: 30px;
        color: white;
    }}
    .header-logo-container {{
        background-color: white; padding: 5px; border-radius: 50%;
        margin-right: 20px; width: 100px; height: 100px;
        display: flex; justify-content: center; align-items: center; overflow: hidden;
    }}
    .header-logo-container img {{ max-width: 90%; max-height: 90%; }}

    /* Profile Sidebar */
    .profile-section {{
        text-align: center; padding: 20px 0;
        background: linear-gradient(180deg, #0097b2 0%, #005f73 100%);
        border-radius: 15px; margin-bottom: 20px;
    }}
    .profile-pic {{ width: 80px; border-radius: 50%; border: 3px solid white; }}
    
    /* Sidebar Headers */
    .sidebar-header-custom {{
        color: white;
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 15px;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
    }}
    </style>
    """, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

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
            
        st.subheader("⚙️ Tetapan Paparan")
        uploaded_file = st.file_uploader("Upload fail CSV", type=["csv"])
        
        st.markdown("---")
        st.subheader("🌍 Mod Peta Interaktif")
        sat_toggle = st.toggle("On/Off Peta Interaktif (Satelit)", value=True)
        
        map_selection = "Satalit (Hybrid)"
        if sat_toggle:
            map_selection = st.radio("Pilih Jenis Peta:", ["Satalit (Hybrid)", "Street Map (Standard)"])
        
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390")

        # Sidebar Gaya Label
        st.markdown("---")
        st.markdown('<div class="sidebar-header-custom">🖊️ Gaya Label</div>', unsafe_allow_html=True)
        
        show_area_label = st.checkbox("Papar Label LUAS", value=True)
        station_circle_size = st.slider("Saiz Bulatan Stesen", 10, 40, 22)
        bearing_font_size = st.slider("Saiz Bearing/Jarak", 5, 12, 7)
        area_font_size = st.slider("Saiz Tulisan LUAS", 10, 20, 14)
        station_label_offset = st.slider("Jarak Label Stesen ke Luar", 0.1, 3.0, 1.5, 0.1)

        st.markdown("---")
        st.subheader("💾 Eksport Data")
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    # Header dengan Video
    video_tag = f'<video autoplay loop muted playsinline id="video-bg"><source src="data:video/mp4;base64,{vid_base64}" type="video/mp4"></video>' if vid_base64 else ''
    logo_tag = f'<img src="data:image/png;base64,{img_base64}">' if img_base64 else ''
    
    st.markdown(f"""
        <div class="header-container">
            {video_tag}
            <div class="header-overlay"></div>
            <div class="header-content">
                <div class="header-logo-container">{logo_tag}</div>
                <div class="header-text">
                    <h1 style="margin:0; font-size: 35pt;">LOT 11487</h1>
                    <p style="margin:0; opacity:0.9;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            
            if all(x in df.columns for x in ['E', 'N', 'STN']):
                # Transformasi Koordinat ke WGS84 untuk Peta
                transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['E'].values, df['N'].values)
                df_mapped = df.copy()
                df_mapped['lat'] = lat
                df_mapped['lon'] = lon
                
                # Geometri & Data Eksport
                coords_local = list(zip(df_mapped['E'], df_mapped['N']))
                if coords_local[0] != coords_local[-1]: coords_local.append(coords_local[0])
                poly_local = Polygon(coords_local)
                
                # 1. KIRA LUAS SECARA AUTOMATIK DARI GEOMETRI (override manual dipadam)
                calculated_area = poly_local.area
                
                coords_wgs = list(zip(df_mapped['lon'], df_mapped['lat']))
                if coords_wgs[0] != coords_wgs[-1]: coords_wgs.append(coords_wgs[0])
                poly_wgs = Polygon(coords_wgs)

                # Eksport GeoJSON (menggunakan luas yang dikira)
                with st.sidebar:
                    geojson_data = mapping(poly_wgs)
                    feature = {
                        "type": "FeatureCollection",
                        "features": [{
                            "type": "Feature",
                            "geometry": geojson_data,
                            "properties": {"Area_m2": calculated_area, "Lot": "11487"}
                        }]
                    }
                    st.download_button(
                        label="🚀 Eksport ke QGIS (GeoJSON)",
                        data=json.dumps(feature),
                        file_name="lot_11487.geojson",
                        mime="application/json",
                        use_container_width=True
                    )

                # Kira Bearing & Jarak (Local Coordinates)
                bearings = []
                distances = []
                midpoints_local = []
                midpoints_wgs = []

                for i in range(len(df_mapped)):
                    p1_local = (df_mapped.iloc[i]['E'], df_mapped.iloc[i]['N'])
                    p1_wgs = (df_mapped.iloc[i]['lon'], df_mapped.iloc[i]['lat'])
                    
                    if i == len(df_mapped) - 1: # Tutup loop kembali ke titik pertama
                        p2_local = (df_mapped.iloc[0]['E'], df_mapped.iloc[0]['N'])
                        p2_wgs = (df_mapped.iloc[0]['lon'], df_mapped.iloc[0]['lat'])
                    else:
                        p2_local = (df_mapped.iloc[i+1]['E'], df_mapped.iloc[i+1]['N'])
                        p2_wgs = (df_mapped.iloc[i+1]['lon'], df_mapped.iloc[i+1]['lat'])
                    
                    bearing_str, dist = calculate_bearing_distance(p1_local, p2_local)
                    bearings.append(bearing_str)
                    distances.append(dist)
                    
                    # Kira Titik Tengah untuk Label
                    mid_e = (p1_local[0] + p2_local[0]) / 2
                    mid_n = (p1_local[1] + p2_local[1]) / 2
                    midpoints_local.append((mid_e, mid_n))
                    
                    mid_lon = (p1_wgs[0] + p2_wgs[0]) / 2
                    mid_lat = (p1_wgs[1] + p2_wgs[1]) / 2
                    midpoints_wgs.append((mid_lat, mid_lon))

                # ================== PAPARAN UTAMA ==================
                
                if sat_toggle:
                    # ------------------ MOD 1: PETA INTERAKTIF (FOLIUM) ------------------
                    center_lat = df_mapped['lat'].mean()
                    center_lon = df_mapped['lon'].mean()
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=19, max_zoom=22)

                    # Tentukan Tile Google Maps
                    tile_type = 'y' if map_selection == "Satalit (Hybrid)" else 'm'
                    folium.TileLayer(
                        tiles=f'https://mt1.google.com/vt/lyrs={tile_type}&x={{x}}&y={{y}}&z={{z}}',
                        attr='Google Maps', name='Google Maps',
                        max_zoom=22, max_native_zoom=20, overlay=False
                    ).add_to(m)
                    
                    # Lukis Poligon
                    folium.Polygon(
                        [[lat, lon] for lon, lat in coords_wgs], 
                        color="yellow", weight=3, fill=True, fill_opacity=0.2
                    ).add_to(m)

                    # Papar Luas (Menggunakan luas yang dikira)
                    if show_area_label:
                        folium.Marker(
                            [center_lat, center_lon],
                            icon=folium.DivIcon(html=f'<div style="color: #2ecc71; font-weight: bold; font-size: {area_font_size}pt; text-shadow: 2px 2px black; background: white; padding: 2px 5px; border-radius: 5px; border: 1px solid #2ecc71;">{calculated_area:.2f} m²</div>')
                        ).add_to(m)
                    
                    # Papar Bearing & Jarak
                    for i, midpoint in enumerate(midpoints_wgs):
                        label_html = f'<div style="color: yellow; font-size: {bearing_font_size}pt; font-weight: bold; text-shadow: 1px 1px black; text-align: center; line-height: 1.1; width: max-content;">{bearings[i]}<br>{distances[i]:.2f}m</div>'
                        folium.Marker(
                            midpoint,
                            icon=folium.DivIcon(html=label_html)
                        ).add_to(m)

                    # Marker Stesen
                    for _, row in df_mapped.iterrows():
                        folium.Marker(
                            [row['lat'], row['lon']],
                            icon=folium.DivIcon(html=f'<div style="color: white; background: red; border-radius: 50%; width: {station_circle_size}px; height: {station_circle_size}px; text-align: center; font-size: 10pt; font-weight: bold; border: 2px solid white; display: flex; align-items: center; justify-content: center;">{int(row["STN"])}</div>')
                        ).add_to(m)

                    folium_static(m, width=1100, height=550)

                else:
                    # ------------------ MOD 2: GRAF PLOT LOCAL (MATPLOTLIB) ------------------
                    st.markdown("### 📊 Plot Koordinat Tempatan (Graf)")
                    
                    fig, ax = plt.subplots(figsize=(12, 8))
                    
                    # 2. BERSIHKAN GARISAN PUTIH (axis spines & grid)
                    ax.axis('off') # Ini membuang semua kotak axis dan garisan grid
                    
                    # Data Plot
                    plot_data = np.array(coords_local)
                    e_coords = plot_data[:, 0]
                    n_coords = plot_data[:, 1]
                    
                    # Lukis Poligon & Sempadan (Kekal Style Kuning/Ungu)
                    ax.plot(e_coords, n_coords, color='yellow', linewidth=3, zorder=1)
                    ax.fill(e_coords, n_coords, color='#D8BFD8', alpha=0.5, zorder=0) # Light Purple

                    # Label Bearing & Jarak di tengah-tengah garisan
                    for i, mid_p in enumerate(midpoints_local):
                        p1 = coords_local[i]
                        p2 = coords_local[i+1]
                        
                        dx = p2[0] - p1[0]
                        dy = p2[1] - p1[1]
                        angle_rad = math.atan2(dy, dx)
                        angle_deg = math.degrees(angle_rad)
                        
                        rotation = angle_deg
                        if rotation > 90 or rotation < -90:
                            rotation += 180

                        ax.text(mid_p[0], mid_p[1], f"{bearings[i]}\n{distances[i]:.2f}m",
                                color='red', fontsize=bearing_font_size + 2, fontweight='bold', 
                                ha='center', va='center', rotation=rotation, rotation_mode='anchor', zorder=3)

                    # Label Luas di tengah poligon (Menggunakan luas yang dikira)
                    if show_area_label:
                        centroid = poly_local.centroid
                        ax.text(centroid.x, centroid.y, f"{calculated_area:.2f} m²",
                                color='#2ecc71', fontsize=area_font_size + 2, fontweight='bold', 
                                ha='center', va='center', zorder=4,
                                bbox=dict(facecolor='white', edgecolor='#2ecc71', boxstyle='round,pad=0.3'))
                    
                    # Plot Bulatan Stesen & Label Nombor
                    for i, row in df_mapped.iterrows():
                        ax.scatter(row['E'], row['N'], color='red', edgecolor='white', s=station_circle_size*5, zorder=5)
                        
                        ax.annotate(str(int(row['STN'])), (row['E'], row['N']),
                                    xytext=(station_label_offset * 5, station_label_offset * 5),
                                    textcoords='offset points', color='black', fontsize=12,
                                    fontweight='bold', zorder=6)

                    # Had Axis Graf (Kekal teknikal)
                    ax.set_aspect('equal') # Pastikan skala E dan N sama
                    
                    st.pyplot(fig)

                # Papar Jadual Data
                st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
        except Exception as e:
            st.error(f"Ralat Proses Fail CSV: {e}")
    else:
        st.info("Sila muat naik fail CSV di sidebar.")
