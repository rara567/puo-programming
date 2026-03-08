import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide")

# Custom CSS untuk menyamakan gaya dengan gambar
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #262730;
        color: white;
        border: 1px solid #4B4B4B;
    }
    .stButton>button:hover {
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    .title-container {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        border-left: 10px solid #2E86C1;
        margin-bottom: 20px;
    }
    .title-text {
        color: #1B1B1B;
        font-size: 45px;
        font-weight: bold;
        margin-bottom: 0;
    }
    .subtitle-text {
        color: #5D6D7E;
        font-size: 18px;
    }
    </style>
    """, unsafe_allow_html=True)

# ================== LOGIK SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================== FUNGSI PEMPROSESAN ==================
def transform_coords(df, from_epsg):
    try:
        # Menukar koordinat ke WGS84 untuk paparan peta
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
    cols = st.columns([1, 2, 1])
    with cols[1]:
        st.markdown("### 🔐 Akses Sistem Visualisasi Lot")
        user_id = st.text_input("ID Pengguna")
        password = st.text_input("Kata Laluan", type="password")
        
        if st.button("Log Masuk"):
            if user_id == "1" and password == "admin123":
                st.session_state.logged_in = True
                st.success("Berjaya Log Masuk!")
                st.rerun()
            else:
                st.error("ID atau Kata Laluan Salah")
else:
    # ================== SIDEBAR ==================
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Logo_Politeknik_Malaysia.png/800px-Logo_Politeknik_Malaysia.png", width=150)
        st.markdown("---")
        if st.button("🔑 Tukar Kata Laluan"):
            st.info("Ciri ini akan datang.")
        
        if st.button("🚪 Log Keluar"):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    # Header mengikut gambar
    st.markdown("""
        <div class="title-container">
            <p class="title-text">SISTEM SURVEY LOT</p>
            <p class="subtitle-text">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam</p>
        </div>
        """, unsafe_allow_html=True)

    # Input Section
    col1, col2 = st.columns([1, 2])
    
    with col1:
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390", help="Contoh: 3384 (Cassini Perak), 4326 (WGS84)")
        
    with col2:
        uploaded_file = st.file_uploader("📂 Muat naik fail CSV (STN, E, N)", type=["csv"])

    # Processing Data
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            
            if all(x in df.columns for x in ['E', 'N', 'STN']):
                # Transformasi
                df_mapped = transform_coords(df.copy(), epsg_code)
                
                if df_mapped is not None:
                    # Kira Luas
                    coords = list(zip(df['E'], df['N']))
                    poly = Polygon(coords)
                    area = poly.area
                    
                    # Paparan Metrik
                    m1, m2 = st.columns(2)
                    m1.metric("Luas (m²)", f"{area:.2f}")
                    m2.metric("Bilangan Titik", len(df))

                    # Peta
                    st.markdown("### 🗺️ Paparan Lokasi")
                    center_lat = df_mapped['lat'].mean()
                    center_lon = df_mapped['lon'].mean()
                    
                    m = folium.Map(location=[center_lat, center_lon], zoom_start=18)
                    
                    # Layer Satelit
                    google_sat = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}'
                    folium.TileLayer(tiles=google_sat, attr='Google', name='Satelit').add_to(m)
                    
                    # Lukis Sempadan
                    locations = df_mapped[['lat', 'lon']].values.tolist()
                    folium.Polygon(locations, color="yellow", weight=5, fill=True, fill_opacity=0.2).add_to(m)
                    
                    # Titik Stesen
                    for _, row in df_mapped.iterrows():
                        folium.CircleMarker(
                            [row['lat'], row['lon']], 
                            radius=3, color="red", popup=f"STN: {row['STN']}"
                        ).add_to(m)

                    folium_static(m, width=1000)
            else:
                st.error("Fail CSV mesti mempunyai kolum: STN, E, N")
        except Exception as e:
            st.error(f"Ralat pemprosesan: {e}")
    else:
        st.info("Sila muat naik fail CSV untuk melihat visualisasi.")
