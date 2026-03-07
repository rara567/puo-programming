import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon, LineString
import folium
from streamlit_folium import folium_static
from pyproj import Transformer

# ================== FUNGSI PENUKARAN KOORDINAT ==================
def transform_coords(df, from_epsg):
    try:
        transformer = Transformer.from_crs(f"EPSG:{from_epsg}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        df['lat'] = lat
        df['lon'] = lon
        return df
    except Exception as e:
        st.error(f"Ralat transformasi koordinat: {e}")
        return df

# ================== FUNGSI LOGIN ==================
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    
    st.title("🔐 Akses Sistem Visualisasi Lot")
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
    st.set_page_config(page_title="PUO Geomatics - Visualisasi Lot", layout="wide")

    st.title("📌 POLITEKNIK UNGKU OMAR")
    st.caption("Sistem Visualisasi Lot Tanah & Satelit Interaktif")

    # ================== SIDEBAR ==================
    st.sidebar.header("⚙️ Tetapan Data")
    uploaded_file = st.sidebar.file_uploader("Upload fail CSV (E, N, STN)", type=["csv"])
    
    crs_choice = st.sidebar.selectbox(
        "Sistem Koordinat Fail Anda:",
        ["Perak Cassini (Meter)", "RSO Malaysia (Meter)", "WGS84 (Decimal Degrees)"]
    )
    
    view_mode = st.sidebar.radio("Pilih Mod Paparan:", ["Peta Satelit Interaktif", "Pelan Teknikal (Matplotlib)"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🖋️ Gaya Visual")
    label_size_stn = st.sidebar.slider("Saiz No Stesen", 6, 20, 10)
    label_size_luas = st.sidebar.slider("Saiz Tulisan LUAS", 8, 40, 15)
    
    # ================== PEMPROSESAN DATA ==================
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]

            if not all(col in df.columns for col in ['E', 'N', 'STN']):
                st.error("Ralat: Fail CSV mesti ada kolum 'E', 'N', dan 'STN'")
                st.stop()

            # 1. Transformasi Koordinat
            df_map = df.copy()
            if "Perak Cassini" in crs_choice:
                df_map = transform_coords(df_map, 3384)
            elif "RSO Malaysia" in crs_choice:
                df_map = transform_coords(df_map, 3168)
            else:
                df_map['lat'] = df_map['N']
                df_map['lon'] = df_map['E']

            # 2. Kira Geometri
            coords_orig = list(zip(df['E'], df['N']))
            poly_geom = Polygon(coords_orig)
            line_geom = LineString(coords_orig + [coords_orig[0]])
            centroid = poly_geom.centroid
            area_m2 = poly_geom.area

            # Metrik
            m1, m2, m3 = st.columns(3)
            m1.metric("Luas (m²)", f"{area_m2:.2f}")
            m2.metric("Luas (Ekar)", f"{area_m2/4046.856:.4f}")
            m3.metric("Bilangan Stesen", len(df))

            # ================== MOD 1: PETA SATELIT (FOLIUM) ==================
            if view_mode == "Peta Satelit Interaktif":
                st.markdown("### 🛰️ Paparan Google Satellite Hybrid")
                
                center_lat, center_lon = df_map['lat'].mean(), df_map['lon'].mean()
                
                # Cipta peta tanpa tiles default
                m = folium.Map(location=[center_lat, center_lon], zoom_start=19, tiles=None)

                # Tambah Google Satellite sebagai BASE LAYER (overlay=False)
                # lyrs=y (Hybrid), lyrs=s (Satelit Sahaja)
                folium.TileLayer(
                    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                    attr='Google Maps',
                    name='Google Satellite',
                    overlay=False,
                    control=True
                ).add_to(m)

                # Tambah OpenStreetMap sebagai pilihan kedua
                folium.TileLayer(
                    tiles='openstreetmap',
                    name='OpenStreetMap',
                    overlay=False,
                    control=True
                ).add_to(m)

                # Lukis Poligon
                folium_coords = df_map[['lat', 'lon']].values.tolist()
                folium.Polygon(
                    locations=folium_coords,
                    color="cyan",
                    weight=4,
                    fill=True,
                    fill_color="yellow",
                    fill_opacity=0.2,
                    popup=f"Luas: {area_m2:.2f} m²"
                ).add_to(m)

                # Tambah Marker
                for _, row in df_map.iterrows():
                    folium.CircleMarker(
                        location=[row['lat'], row['lon']],
                        radius=5,
                        color="red",
                        fill=True,
                        fill_opacity=1,
                        tooltip=f"STN: {int(row['STN'])}"
                    ).add_to(m)

                m.fit_bounds(folium_coords)
                
                # PENTING: LayerControl mesti diletakkan paling akhir
                folium.LayerControl(collapsed=False, position='topright').add_to(m)
                
                folium_static(m, width=1100, height=600)

            # ================== MOD 2: PELAN TEKNIKAL ==================
            else:
                st.markdown("### 📐 Pelan Teknikal (Unit: Meter)")
                fig, ax = plt.subplots(figsize=(10, 8))
                x, y = line_geom.xy
                ax.plot(x, y, linewidth=2, color='black')
                ax.fill(x, y, color='green', alpha=0.1)
                
                ax.text(centroid.x, centroid.y, f"LUAS\n{area_m2:.2f} m²", 
                        fontsize=label_size_luas, fontweight='bold', ha='center',
                        bbox=dict(boxstyle='round', fc='white', alpha=0.7))

                for _, row in df.iterrows():
                    ax.scatter(row['E'], row['N'], color='red')
                    ax.text(row['E'], row['N'], f" {int(row['STN'])}", fontsize=label_size_stn)

                ax.set_aspect("equal")
                ax.grid(True, linestyle='--', alpha=0.5)
                st.pyplot(fig)

        except Exception as e:
            st.error(f"⚠️ Ralat: {e}")
    else:
        st.info("👋 Sila upload fail CSV untuk bermula.")
