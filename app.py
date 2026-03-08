import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from pyproj import Transformer
from shapely.geometry import Polygon
import io

# ================== KONFIGURASI HALAMAN ==================
st.set_page_config(page_title="Sistem Survey Lot - PUO", layout="wide", page_icon="📍")

# Custom CSS untuk gaya profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .title-container {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 25px;
    }
    .title-text { font-size: 38px; font-weight: 800; margin-bottom: 0; }
    .subtitle-text { font-size: 16px; opacity: 0.9; }
    </style>
    """, unsafe_allow_html=True)

# ================== LOGIK SESSION STATE ==================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ================== FUNGSI PEMPROSESAN ==================
def transform_coords(df, from_epsg):
    try:
        # Menukar koordinat ke WGS84 (Lat/Lon)
        transformer = Transformer.from_crs(f"EPSG:{from_epsg}", "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(df['E'].values, df['N'].values)
        df['lat'] = lat
        df['lon'] = lon
        return df
    except Exception as e:
        st.error(f"Ralat Kod EPSG tidak sah: {e}")
        return None

# ================== HALAMAN LOGIN ==================
if not st.session_state.logged_in:
    cols = st.columns([1, 1.5, 1])
    with cols[1]:
        st.write("") 
        st.write("") 
        with st.container():
            st.markdown("<h2 style='text-align: center;'>🔐 Log Masuk Sistem</h2>", unsafe_allow_html=True)
            user_id = st.text_input("ID Pengguna (Sila masukkan 67)")
            password = st.text_input("Kata Laluan", type="password")
            
            if st.button("Masuk Sekarang", use_container_width=True):
                if user_id == "67" and password == "ikmalkacak":
                    st.session_state.logged_in = True
                    st.success("Akses Dibenarkan!")
                    st.rerun()
                else:
                    st.error("ID atau Kata Laluan Salah")
else:
    # ================== SIDEBAR ==================
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/01/Logo_Politeknik_Malaysia.png/800px-Logo_Politeknik_Malaysia.png", width=180)
        st.title("Menu Kawalan")
        st.info(f"Log masuk sebagai: ID 67")
        
        st.markdown("---")
        epsg_code = st.text_input("🔵 Kod EPSG:", value="4390", help="Contoh: 3384 (Cassini Perak), 4326 (WGS84)")
        
        if st.button("🚪 Log Keluar", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # ================== KANDUNGAN UTAMA ==================
    st.markdown("""
        <div class="title-container">
            <p class="title-text">SISTEM SURVEY LOT DIGITAL</p>
            <p class="subtitle-text">Politeknik Ungku Omar | Jabatan Kejuruteraan Awam & Geomatik</p>
        </div>
        """, unsafe_allow_html=True)

    # Kawasan Muat Naik
    uploaded_file = st.file_uploader("📂 Pilih fail CSV anda (Format: STN, E, N)", type=["csv"])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = [c.strip().upper() for c in df.columns]
            
            if all(x in df.columns for x in ['E', 'N', 'STN']):
                df_mapped = transform_coords(df.copy(), epsg_code)
                
                if df_mapped is not None:
                    # Pengiraan Geometrik
                    coords = list(zip(df['E'], df['N']))
                    poly = Polygon(coords)
                    area_sqm = poly.area
                    perimeter = poly.length
                    
                    # Paparan Statistik (Metrik)
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Luas (m²)", f"{area_sqm:,.3f}")
                    m2.metric("Luas (Ekar)", f"{(area_sqm * 0.000247105):.4f}")
                    m3.metric("Perimeter (m)", f"{perimeter:.2f}")
                    m4.metric("Jumlah Titik", len(df))

                    st.markdown("---")
                    
                    # Bahagian Peta dan Jadual
                    tab1, tab2 = st.tabs(["🗺️ Visualisasi Peta", "📊 Data Jadual"])
                    
                    with tab1:
                        center_lat = df_mapped['lat'].mean()
                        center_lon = df_mapped['lon'].mean()
                        
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=19, control_scale=True)
                        
                        # Layer Pilihan
                        folium.TileLayer('openstreetmap', name='Peta Jalan').add_to(m)
                        google_sat = folium.TileLayer(
                            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                            attr='Google Hybrid',
                            name='Satelit (Hybrid)',
                            overlay=False,
                            control=True
                        ).add_to(m)
                        
                        # Lukis Polygon Lot
                        locations = df_mapped[['lat', 'lon']].values.tolist()
                        folium.Polygon(
                            locations, 
                            color="#3498db", 
                            weight=3, 
                            fill=True, 
                            fill_color="#3498db", 
                            fill_opacity=0.3,
                            tooltip="Kawasan Lot Survey"
                        ).add_to(m)
                        
                        # Tambah Penanda Titik & Label
                        for _, row in df_mapped.iterrows():
                            folium.CircleMarker(
                                [row['lat'], row['lon']], 
                                radius=4, 
                                color="red", 
                                fill=True,
                                popup=f"Stesen: {row['STN']}<br>E: {row['E']}<br>N: {row['N']}"
                            ).add_to(m)
                            
                            # Label Stesen
                            folium.Marker(
                                [row['lat'], row['lon']],
                                icon=folium.DivIcon(html=f"""<div style="font-family: sans-serif; color: yellow; font-weight: bold; font-size: 10pt; text-shadow: 1px 1px #000;">{row['STN']}</div>""")
                            ).add_to(m)

                        folium.LayerControl().add_to(m)
                        folium_static(m, width=1100, height=550)

                    with tab2:
                        st.dataframe(df_mapped[['STN', 'E', 'N', 'lat', 'lon']], use_container_width=True)
                        
                        # Fungsi Download Data Baru
                        csv = df_mapped.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Muat Turun Data Berproses (CSV)",
                            data=csv,
                            file_name='hasil_survey_lot.csv',
                            mime='text/csv',
                        )

            else:
                st.error("Ralat: Fail CSV mesti mengandungi kolum STN, E, dan N.")
        except Exception as e:
            st.error(f"Ralat Sistem: {e}")
    else:
        # Paparan Info jika tiada fail
        st.info("Sila muat naik fail koordinat (CSV) untuk memulakan pengiraan dan pemetaan.")
        with st.expander("Klik untuk lihat contoh format CSV"):
            st.code("""
STN,E,N
1,453201.123,345678.456
2,453220.456,345680.123
3,453215.789,345695.789
            """)
