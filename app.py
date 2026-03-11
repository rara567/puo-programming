import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon
import base64
import os
import math
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MatplotlibPolygon

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide", page_icon="📍")

LOGO_PATH = "puo.png" 
VIDEO_PATH = "video.mp4" 

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
    if bearing_deg < 0: bearing_deg += 360
    
    rotation = math.degrees(math.atan2(dn, de))
    if rotation > 90: rotation -= 180
    if rotation < -90: rotation += 180
        
    return format_bearing(bearing_deg), distance, rotation

img_base64 = get_base64_file(LOGO_PATH)
vid_base64 = get_base64_file(VIDEO_PATH)

# ================== CUSTOM CSS ==================
st.markdown(f"""
    <style>
    [data-testid="stSidebar"] {{ background-color: #1E1E1E; color: white; }}
    .header-container {{ position: relative; width: 100%; height: 200px; overflow: hidden; border-radius: 15px; margin-bottom: 20px; border-bottom: 5px solid #d35400; display: flex; align-items: center; background-color: black; }}
    #video-bg {{ position: absolute; top: 50%; left: 50%; min-width: 100%; min-height: 100%; transform: translate(-50%, -50%); object-fit: cover; z-index: 0; }}
    .header-overlay {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.4); z-index: 1; }}
    .header-content {{ position: relative; z-index: 2; display: flex; align-items: center; padding-left: 30px; color: white; }}
    .header-logo-container {{ background-color: white; padding: 5px; border-radius: 50%; margin-right: 20px; width: 100px; height: 100px; display: flex; justify-content: center; align-items: center; overflow: hidden; }}
    .header-logo-container img {{ max-width: 90%; max-height: 90%; }}
    .profile-section {{ text-align: center; padding: 20px 0; background: linear-gradient(180deg, #0097b2 0%, #005f73 100%); border-radius: 15px; margin-bottom: 20px; }}
    .profile-pic {{ width: 80px; border-radius: 50%; border: 3px solid white; }}
    
    /* Login Interface Styling */
    .login-box {{
        background: rgba(255, 255, 255, 0.05);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }}
    </style>
    """, unsafe_allow_html=True)

# ================== SISTEM LOG IN & LUPA KATA LALUAN ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "reset_mode" not in st.session_state:
    st.session_state.reset_mode = False
if "stored_password" not in st.session_state:
    st.session_state.stored_password = "ikmalkacak" 

if not st.session_state.logged_in:
    cols = st.columns([1, 1.2, 1])
    
    with cols[1]:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/5087/5087579.png", width=100)
        st.title("Survey Lot Rumah")
        
        if not st.session_state.reset_mode:
            # --- Paparan Log In ---
            user_id = st.text_input("👤 Masukkan ID:", placeholder="Contoh: 67")
            password = st.text_input("🔑 Masukkan Kata Laluan:", type="password")
            
            if st.button("Log Masuk", use_container_width=True, type="primary"):
                if user_id == "67" and password == st.session_state.stored_password:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan Salah!")
            
            # Guna st.button biasa tanpa variant untuk elak ralat
            if st.button("❓ Lupa Kata Laluan?"):
                st.session_state.reset_mode = True
                st.rerun()
        
        else:
            # --- Paparan Lupa Kata Laluan ---
            st.subheader("Set Semula Kata Laluan")
            verify_id = st.text_input("Sila masukkan ID anda:")
            secret_hint = st.text_input("Siapakah nama pensyarah kegemaran anda? (Hint: Jawapan adalah 'PUO')", type="password")
            
            new_password = st.text_input("Masukkan Kata Laluan Baru:", type="password")
            confirm_password = st.text_input("Sahkan Kata Laluan Baru:", type="password")
            
            col_reset1, col_reset2 = st.columns(2)
            with col_reset1:
                if st.button("Batal", use_container_width=True):
                    st.session_state.reset_mode = False
                    st.rerun()
            with col_reset2:
                if st.button("Simpan", use_container_width=True, type="primary"):
                    if verify_id == "67" and secret_hint.lower() == "puo":
                        if new_password == confirm_password and len(new_password) > 0:
                            st.session_state.stored_password = new_password
                            st.success("Berjaya dikemaskini!")
                            st.session_state.reset_mode = False
                            st.rerun()
                        else:
                            st.error("Kata laluan tidak sepadan!")
                    else:
                        st.error("Maklumat pengesahan salah!")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # ================== SIDEBAR ==================
    with st.sidebar:
        st.markdown('<div class="profile-section"><img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" class="profile-pic"><h3 style="color:white; margin-top:10px;">Hai, Hzzrull!</h3><p style="color:white; opacity:0.8;">Student</p></div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("Upload fail CSV", type=["csv"])
        sat_toggle = st.toggle("On/Off Peta Interaktif (Satelit)", value=True)
        map_selection = st.radio("Pilih Jenis Peta:", ["Satalit (Hybrid)", "Street Map (Standard)"]) if sat_toggle else "Satalit (Hybrid)"
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390")
        
        st.markdown("---")
        st.subheader("🖋️ Gaya Label")
        show_area_label = st.checkbox("Papar Label LUAS", value=True)
        station_circle_size = st.slider("Saiz Bulatan Stesen", 10, 40, 22)
        bearing_font_size = st.slider("Saiz Bearing/Jarak", 5, 15, 9)
        area_font_size = st.slider("Saiz Tulisan LUAS", 10, 30, 20)
        station_label_offset = st.slider("Jarak Label Stesen ke Luar", 0.1, 3.0, 1.5, 0.1)

        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== MAIN CONTENT ==================
    video_tag = f'<video autoplay loop muted playsinline id="video-bg"><source src="data:video/mp4;base64,{vid_base64}" type="video/mp4"></video>' if vid_base64 else ''
    logo_tag = f'<img src="data:image/png;base64,{img_base64}">' if img_base64 else ''
    st.markdown(f'<div class="header-container">{video_tag}<div class="header-overlay"></div><div class="header-content"><div class="header-logo-container">{logo_tag}</div><div><h1 style="margin:0; font-size: 35pt;">LOT 11487</h1><p style="margin:0; opacity:0.9;">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p></div></div></div>', unsafe_allow_html=True)

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            
            transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4326", always_xy=True)
            lon, lat = transformer.transform(df['E'].values, df['N'].values)
            df_mapped = df.assign(lat=lat, lon=lon)
            
            coords_local = list(zip(df_mapped['E'], df_mapped['N']))
            coords_local.append(coords_local[0])
            poly_obj = Polygon(coords_local)
            calculated_area = poly_obj.area 

            bearings, distances, rotations, mid_l, mid_w = [], [], [], [], []
            for i in range(len(df_mapped)):
                p1, p2 = coords_local[i], coords_local[i+1]
                b, d, r = calculate_bearing_distance(p1, p2)
                bearings.append(b); distances.append(d); rotations.append(r)
                mid_l.append(((p1[0]+p2[0])/2, (p1[1]+p2[1])/2))
                
                p1_gps = (df_mapped.iloc[i]['lat'], df_mapped.iloc[i]['lon'])
                p2_gps = (df_mapped.iloc[0]['lat'] if i==len(df_mapped)-1 else df_mapped.iloc[i+1]['lat'],
                          df_mapped.iloc[0]['lon'] if i==len(df_mapped)-1 else df_mapped.iloc[i+1]['lon'])
                mid_w.append(((p1_gps[0]+p2_gps[0])/2, (p1_gps[1]+p2_gps[1])/2))

            if sat_toggle:
                m = folium.Map(location=[df_mapped['lat'].mean(), df_mapped['lon'].mean()], zoom_start=20)
                t_type = 'y' if map_selection == "Satalit (Hybrid)" else 'm'
                folium.TileLayer(tiles=f'https://mt1.google.com/vt/lyrs={t_type}&x={{x}}&y={{y}}&z={{z}}', attr='Google', max_zoom=22).add_to(m)
                
                folium.Polygon([[la, lo] for lo, la in list(zip(df_mapped['lon'], df_mapped['lat']))+[(df_mapped['lon'][0], df_mapped['lat'][0])]], 
                               color="yellow", weight=3, fill=True, fill_opacity=0.2).add_to(m)
                
                if show_area_label:
                    folium.Marker([df_mapped['lat'].mean(), df_mapped['lon'].mean()], 
                                  icon=folium.DivIcon(html=f'''<div style="color: #00FF00; font-weight: 900; font-size: {area_font_size}pt; 
                                  text-shadow: 2px 2px 4px #000; white-space: nowrap; transform: translate(-50%, -50%);">
                                  {calculated_area:.2f} m²</div>''')).add_to(m)
                
                for i, mp in enumerate(mid_w):
                    folium.Marker(mp, icon=folium.DivIcon(html=f'''
                        <div style="color: #ffff00; font-family: 'Arial Black', sans-serif; font-size: {bearing_font_size}pt; 
                            font-weight: bold; text-align: center; text-shadow: 1px 1px 2px #000; width: 150px;
                            transform: translate(-50%, -50%) rotate({-rotations[i]}deg);">
                            {bearings[i]}<br><span style="color: white;">{distances[i]:.2f}m</span>
                        </div>''')).add_to(m)
                
                for _, r in df_mapped.iterrows():
                    folium.Marker([r['lat'], r['lon']], icon=folium.DivIcon(html=f'''
                        <div style="color:white; background:red; border-radius:50%; width:{station_circle_size}px; height:{station_circle_size}px; 
                        text-align:center; font-weight:bold; border:2px solid white; display:flex; align-items:center; justify-content:center;
                        font-size: {station_circle_size/2}px; transform: translate(-50%, -50%);">
                        {int(r["STN"])}</div>''')).add_to(m)
                
                folium_static(m, width=1100, height=550)
            
            else:
                fig, ax = plt.subplots(figsize=(10, 8))
                pts = np.array(coords_local)
                ax.set_axis_off() 
                ax.add_patch(MatplotlibPolygon(pts, facecolor='#D8BFD8', alpha=0.8, zorder=1))
                ax.plot(pts[:,0], pts[:,1], color='yellow', linewidth=3, zorder=2)

                for i, ml in enumerate(mid_l):
                    ax.text(ml[0], ml[1], f"{bearings[i]}\n{distances[i]:.2f}m", 
                            color='brown', fontsize=bearing_font_size+3, fontweight='bold', ha='center', va='center', 
                            rotation=rotations[i], zorder=4)

                if show_area_label:
                    cx, cy = poly_obj.centroid.x, poly_obj.centroid.y
                    ax.text(cx, cy, f"{calculated_area:.2f} m²", color='green', fontsize=area_font_size, 
                            fontweight='bold', ha='center', zorder=5, bbox=dict(facecolor='white', edgecolor='green', boxstyle='round,pad=0.3'))
                
                for _, r in df_mapped.iterrows():
                    ax.scatter(r['E'], r['N'], color='red', s=station_circle_size*8, zorder=6, edgecolors='white', linewidth=1.5)
                    ax.text(r['E'], r['N'], str(int(r['STN'])), color='white', ha='center', va='center', fontsize=9, fontweight='bold', zorder=7)
                
                ax.set_aspect('equal')
                st.pyplot(fig)

            st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']].style.format(precision=3), use_container_width=True)
            
        except Exception as e:
            st.error(f"Ralat: {e}")
