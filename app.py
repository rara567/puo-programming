import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, Point, LineString
import json
import os
import folium
from streamlit_folium import folium_static

# ================== FUNGSI TUKAR DMS ==================
def format_dms(decimal_degree):
    d = int(decimal_degree)
    m = int((decimal_degree - d) * 60)
    s = round((((decimal_degree - d) * 60) - m) * 60, 0)
    return f"{d}°{abs(m):02d}'{abs(int(s)):02d}\""

# ================== FUNGSI LOGIN ==================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔐 Akses Sistem")
    password = st.text_input("Sila masukkan Kata Laluan", type="password")
    if st.button("Log Masuk"):
        if password == "admin123":
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("😕 Kata laluan salah.")
    return False

# ================== MAIN APP ==================
if check_password():
    st.set_page_config(page_title="Visualisasi Poligon Pro + Satelit", layout="wide")

    # --- HEADER & LOGO ---
    current_dir = os.path.dirname(os.path.abspath(__file__))
    col_logo, col_text = st.columns([1, 8])
    with col_logo:
        logo_path = os.path.join(current_dir, "puo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=100)
        else:
            st.markdown("🏢")

    with col_text:
        st.title("POLITEKNIK UNGKU OMAR")
        st.subheader("Sistem Visualisasi Lot Tanah & Satelit")

    # ================== SIDEBAR ==================
    st.sidebar.header("⚙️ Tetapan Data & Paparan")
    uploaded_file = st.sidebar.file_uploader("Upload fail CSV (E, N, STN)", type=["csv"])
    
    view_mode = st.sidebar.radio("Pilih Mod Paparan:", ["Peta Satelit Interaktif", "Pelan Teknikal (Matplotlib)"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🖋️ Gaya Label (Pelan Teknikal)")
    label_size_stn = st.sidebar.slider("Saiz Label Stesen", 6, 16, 10)
    label_size_data = st.sidebar.slider("Saiz Bearing/Jarak", 5, 12, 7)
    label_size_luas = st.sidebar.slider("Saiz Tulisan LUAS", 8, 30, 15)
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("🌍 Koordinat Sistem")
    st.sidebar.info("Nota: Untuk paparan satelit yang tepat, pastikan koordinat E/N anda adalah dalam format WGS84 (Lat/Lon) atau telah ditukar (Projected).")

    # ================== PEMPROSESAN DATA ==================
    try:
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)
        else:
            data_path = os.path.join(current_dir, "data ukur.csv")
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
            else:
                st.warning("Sila upload fail CSV untuk bermula.")
                st.stop()

        # Geometri Dasar
        coords = list(zip(df['E'], df['N']))
        poly_geom = Polygon(coords)
        line_geom = LineString(coords + [coords[0]])
        centroid = poly_geom.centroid
        area = poly_geom.area

        # Ringkasan Maklumat
        m1, m2, m3 = st.columns(3)
        m1.metric("Luas (m²)", f"{area:.2f}")
        m2.metric("Luas (Ekar)", f"{area/4046.856:.4f}")
        m3.metric("Bilangan Stesen", len(df))

        # ================== MOD 1: PETA SATELIT (FOLIUM) ==================
        if view_mode == "Peta Satelit Interaktif":
            st.markdown("### 🛰️ Hamparan Lot pada Imej Satelit")
            
            # Kita guna purata koordinat untuk center peta
            center_lat, center_lon = df['N'].mean(), df['E'].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=18, control_scale=True)
            
            # Tambah Google Satellite Layer
            google_sat = folium.TileLayer(
                tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr='Google',
                name='Google Satellite',
                overlay=False,
                control=True
            ).add_to(m)
            
            folium.LayerControl().add_to(m)

            # Lukis Poligon Lot
            # Tukar koordinat ke format list [lat, lon] untuk folium
            folium_coords = [[row['N'], row['E']] for _, row in df.iterrows()]
            
            folium.Polygon(
                locations=folium_coords,
                color="yellow",
                weight=3,
                fill=True,
                fill_color="green",
                fill_opacity=0.2,
                popup=f"Luas: {area:.2f} m²"
            ).add_to(m)

            # Tambah Marker bagi setiap Stesen
            for _, row in df.iterrows():
                folium.CircleMarker(
                    location=[row['N'], row['E']],
                    radius=4,
                    color="red",
                    fill=True,
                    tooltip=f"STN: {int(row['STN'])}<br>E: {row['E']}<br>N: {row['N']}"
                ).add_to(m)

            folium_static(m, width=1100, height=600)

        # ================== MOD 2: MATPLOTLIB (TEKNIKAL) ==================
        else:
            st.markdown("### 📐 Pelan Ukur Teknikal")
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.plot(*(line_geom.xy), linewidth=2, color='black', zorder=4)
            ax.fill(*(poly_geom.exterior.xy), color='green', alpha=0.1, zorder=1)
            
            # Grid
            ax.grid(True, linestyle='--', alpha=0.6)
            
            # Label Luas
            ax.text(centroid.x, centroid.y, f"LUAS\n{area:.2f} m²", 
                    fontsize=label_size_luas, fontweight='bold', ha='center',
                    bbox=dict(boxstyle='round', fc='white', alpha=0.8))

            # Loop Data
            for i in range(len(df)):
                p1 = df.iloc[i]
                ax.scatter(p1['E'], p1['N'], color='red', s=40, zorder=5)
                ax.text(p1['E']+0.5, p1['N']+0.5, str(int(p1['STN'])), fontsize=label_size_stn, color='blue')

            ax.set_aspect("equal")
            st.pyplot(fig)

        # ================== EKSPORT DATA ==================
        st.sidebar.markdown("---")
        poly_feature = {"type": "Feature", "properties": {"Luas": area}, "geometry": poly_geom.__geo_interface__}
        geojson_data = json.dumps({"type": "FeatureCollection", "features": [poly_feature]})
        st.sidebar.download_button("📥 Eksport GeoJSON", geojson_data, "lot_tanah.geojson")

    except Exception as e:
        st.error(f"Sila pastikan koordinat E (Longitude) dan N (Latitude) dimasukkan dengan betul. Ralat: {e}")
