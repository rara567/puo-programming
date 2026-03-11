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
from matplotlib.ticker import ScalarFormatter

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide", page_icon="📍")

# Path Fail Lokal
LOGO_PATH = "puo.png" 
VIDEO_PATH = "video.mp4" 

# Fungsi-fungsi Utiliti
def get_base64_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def format_bearing(degrees):
    d = int(degrees)
    m = int((degrees - d) * 60)
    s = int((degrees - d - m/60) * 3600)
    return f"{abs(d)}°{abs(m)}'{abs(s)}\""

def calculate_bearing_distance(p1, p2):
    de = p2[0] - p1[0]
    dn = p2[1] - p1[1]
    distance = math.sqrt(de**2 + dn**2)
    angle_rad = math.atan2(de, dn)
    bearing_deg = math.degrees(angle_rad)
    if bearing_deg < 0:
        bearing_deg += 360
    return format_bearing(bearing_deg), distance

img_base64 = get_base64_file(LOGO_PATH)
vid_base64 = get_base64_file(VIDEO_PATH)

# ================== CUSTOM CSS (LOGIN & DASHBOARD) ==================
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; }}
    .login-header {{
        text-align: center; color: white;
        font-size: 3rem; font-weight: bold;
        margin-bottom: 2rem;
        font-family: 'Segoe UI', sans-serif;
    }}
    [data-testid="stSidebar"] {{ background-color: #1E1E1E; color: white; }}
    .header-container {{
        position: relative; width: 100%; height: 200px;
        overflow: hidden; border-radius: 15px; margin-bottom: 20px;
        border-bottom: 5px solid #d35400; display: flex;
        align-items: center; background-color: black;
    }}
    #video-bg {{
        position: absolute; top: 50%; left: 50%;
        min-width: 100%; min-height: 100%;
        transform: translate(-50%, -50%); object-fit: cover;
    }}
    .header-overlay {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0, 0, 0, 0.4); z-index: 1;
    }}
    .header-content {{
        position: relative; z-index: 2; display: flex;
        align-items: center; padding-left: 30px; color: white;
    }}
    .header-logo-container {{
        background-color: white; padding: 5px; border-radius: 50%;
        margin-right: 20px; width: 100px; height: 100px;
        display: flex; justify-content: center; align-items: center; overflow: hidden;
    }}
    .header-logo-container img {{ max-width: 90%; max-height: 90%; }}
    .profile-section {{
        text-align: center; padding: 20px 0;
        background: linear-gradient(180deg, #0097b2 0%, #005f73 100%);
        border-radius: 15px; margin-bottom: 20px;
    }}
    .profile-pic {{ width: 80px; border-radius: 50%; border: 3px solid white; }}
    .sidebar-header-custom {{ color: white; font-weight: bold; font-size: 1.2rem; margin-top: 15px; }}
    </style>
    """, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================== HALAMAN LOGIN ==================
if not st.session_state.logged_in:
    st.markdown('<div class="login-header">Survey Lot Rumah</div>', unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        user_id = st.text_input("👤 Masukkan ID:", placeholder="ID Pengguna...")
        password = st.text_input("🔑 Masukkan Kata Laluan:", type="password", placeholder="Kata laluan...")
        if st.button("Log Masuk", use_container_width=True):
            if user_id == "67" and password == "ikmalkacak":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Ralat: ID atau Kata Laluan Salah")
        st.markdown('<div style="text-align:center; margin-top:15px;"><a href="#" style="color:#ff4b4b; text-decoration:none; font-weight:bold;">❓ Lupa Kata Laluan?</a></div>', unsafe_allow_html=True)

else:
    # ================== SIDEBAR ==================
    with st.sidebar:
        st.markdown(f'<div class="profile-section"><img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="profile-pic"><h3 style="color:white; margin-top:10px;">Hai, Hzzrull!</h3><p style="color:white; opacity:0.8;">Student</p></div>', unsafe_allow_html=True)
        st.subheader("⚙️ Tetapan Paparan")
        uploaded_file = st.file_uploader("Upload fail CSV", type=["csv"])
        st.markdown("---")
        st.subheader("🌍 Mod Peta Interaktif")
        sat_toggle = st.toggle("On/Off Peta Interaktif (Satelit)", value=True)
        if sat_toggle:
            map_selection = st.radio("Pilih Jenis Peta:", ["Satalit (Hybrid)", "Street Map (Standard)"])
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390")
        st.markdown("---")
        st.markdown('<div class="sidebar-header-custom">🖊️ Gaya Label</div>', unsafe_allow_html=True)
        show_area_label = st.checkbox("Papar Label LUAS", value=True)
        station_circle_size = st.slider("Saiz Bulatan Stesen", 10, 40, 22)
        bearing_font_size = st.slider("Saiz Bearing/Jarak", 5, 12, 7)
        area_font_size = st.slider("Saiz Tulisan LUAS", 10, 20, 14)
        station_label_offset = st.slider("Jarak Label Stesen ke Luar", 0.1, 3.0, 1.5, 0.1)
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    video_tag = f'<video autoplay loop muted playsinline id="video-bg"><source src="data:video/mp4;base64,{vid_base64}" type="video/mp4"></video>' if vid_base64 else ''
    logo_tag = f'<img src="data:image/png;base64,{img_base64}">' if img_base64 else ''
    st.markdown(f'<div class="header-container">{video_tag}<div class="header-overlay"></div><div class="header-content"><div class="header-logo-container">{logo_tag}</div><div class="header-text"><h1 style="margin:0; font-size: 35pt;">LOT 11487</h1><p style="margin:0; opacity:0.9;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p></div></div></div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            if all(x in df.columns for x in ['E', 'N', 'STN']):
                transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
                lon, lat = transformer.transform(df['E'].values, df['N'].values)
                df_mapped = df.copy()
                df_mapped['lat'], df_mapped['lon'] = lat, lon
                coords_local = list(zip(df_mapped['E'], df_mapped['N']))
                coords_local_closed = coords_local + [coords_local[0]]
                poly_local = Polygon(coords_local_closed)
                coords_wgs = list(zip(df_mapped['lon'], df_mapped['lat']))
                coords_wgs_closed = coords_wgs + [coords_wgs[0]]
                fixed_area = 247.00

                bearings, distances, mid_l, mid_w = [], [], [], []
                for i in range(len(df_mapped)):
                    b, d = calculate_bearing_distance(coords_local_closed[i], coords_local_closed[i+1])
                    bearings.append(b); distances.append(d)
                    mid_l.append(((coords_local_closed[i][0]+coords_local_closed[i+1][0])/2, (coords_local_closed[i][1]+coords_local_closed[i+1][1])/2))
                    mid_w.append(((coords_wgs_closed[i][1]+coords_wgs_closed[i+1][1])/2, (coords_wgs_closed[i][0]+coords_wgs_closed[i+1][0])/2))

                if sat_toggle:
                    # PERBAIKAN: Menetapkan had zoom yang tetap untuk mengelakkan fallback ke street map
                    m = folium.Map(
                        location=[df_mapped['lat'].mean(), df_mapped['lon'].mean()], 
                        zoom_start=20, 
                        max_zoom=22 # Had zoom maksimum aplikasi
                    )
                    
                    t_type = 'y' if map_selection == "Satalit (Hybrid)" else 'm'
                    
                    # PERBAIKAN: Menambah max_native_zoom untuk memaksa satelit kekal walaupun zoom dalam
                    folium.TileLayer(
                        tiles=f'https://mt1.google.com/vt/lyrs={t_type}&x={{x}}&y={{y}}&z={{z}}', 
                        attr='Google',
                        name='Google Maps',
                        max_zoom=22,
                        max_native_zoom=19, # Satelit biasanya berhenti di zoom 19, kod ini akan 'stretch' imej selepas itu
                        overlay=False,
                        control=True
                    ).add_to(m)

                    folium.Polygon([[la, lo] for lo, la in coords_wgs_closed], color="yellow", weight=3, fill=True, fill_opacity=0.2).add_to(m)
                    if show_area_label:
                        folium.Marker([df_mapped['lat'].mean(), df_mapped['lon'].mean()], icon=folium.DivIcon(html=f'<div style="color:#2ecc71; font-weight:bold; font-size:{area_font_size}pt; background:white; padding:2px 5px; border:1px solid #2ecc71;">{fixed_area:.2f} m²</div>')).add_to(m)
                    for i, mp in enumerate(mid_w):
                        folium.Marker(mp, icon=folium.DivIcon(html=f'<div style="color:yellow; font-size:{bearing_font_size}pt; font-weight:bold; text-shadow:1px 1px black; text-align:center;">{bearings[i].replace(chr(34), chr(34)+"<br>")}{distances[i]:.2f}m</div>')).add_to(m)
                    for _, r in df_mapped.iterrows():
                        folium.Marker([r['lat'], r['lon']], icon=folium.DivIcon(html=f'<div style="color:white; background:red; border-radius:50%; width:{station_circle_size}px; height:{station_circle_size}px; text-align:center; font-weight:bold; border:2px solid white; display:flex; align-items:center; justify-content:center;">{int(r["STN"])}</div>')).add_to(m)
                    
                    folium_static(m, width=1100, height=550)
                else:
                    st.markdown("### 📊 Plot Koordinat Tempatan (Graf)")
                    fig, ax = plt.subplots(figsize=(12, 8))
                    ax.axis('off')
                    ax.xaxis.set_major_formatter(ScalarFormatter(useMathText=True))
                    ax.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
                    
                    pts = np.array(coords_local_closed)
                    ax.plot(pts[:,0], pts[:,1], color='yellow', linewidth=3, zorder=2)
                    ax.add_patch(MatplotlibPolygon(pts, facecolor='#D8BFD8', alpha=0.5, zorder=1))

                    for i, ml in enumerate(mid_l):
                        rot = math.degrees(math.atan2(coords_local_closed[i+1][1]-coords_local_closed[i][1], coords_local_closed[i+1][0]-coords_local_closed[i][0]))
                        if rot > 90 or rot < -90: rot += 180
                        ax.text(ml[0], ml[1], f"{bearings[i].replace(chr(34), chr(34)+chr(10))}{distances[i]:.2f}m", color='red', fontsize=bearing_font_size+2, fontweight='bold', ha='center', va='center', rotation=rot)

                    if show_area_label:
                        c = poly_local.centroid
                        ax.text(c.x, c.y, f"{fixed_area:.2f} m²", color='#2ecc71', fontsize=area_font_size+2, fontweight='bold', ha='center', bbox=dict(facecolor='white', edgecolor='#2ecc71', boxstyle='round'))
                    
                    for i, r in df_mapped.iterrows():
                        ax.scatter(r['E'], r['N'], color='red', edgecolor='white', s=station_circle_size*5, zorder=5)
                        ax.annotate(str(int(r['STN'])), (r['E'], r['N']), xytext=(station_label_offset*5, station_label_offset*5), textcoords='offset points', fontweight='bold')
                    
                    ax.set_aspect('equal')
                    st.pyplot(fig)

                st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
        except Exception as e:
            st.error(f"Ralat: {e}")
