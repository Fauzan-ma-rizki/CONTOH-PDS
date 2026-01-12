import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster, HeatMap
import os

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Analisis Peluang Usaha UMKM Di Beberapa Daerah Jabar", 
    page_icon="🏙️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DATA KOORDINAT WILAYAH TERPILIH ---
KOTA_COORDS = {
    "Kota Bandung": (-6.9175, 107.6191), 
    "Kab. Bandung": (-7.0251, 107.5197), 
    "Kab. Bandung Barat": (-6.8452, 107.4478), 
    "Kota Bogor": (-6.5971, 106.8060),
    "Kab. Bogor": (-6.4797, 106.8249), 
    "Kota Depok": (-6.4025, 106.7942),
    "Kota Bekasi": (-6.2383, 106.9756), 
    "Kab. Bekasi": (-6.2651, 107.1265), 
    "Kab. Karawang": (-6.3073, 107.2931), 
    "Kab. Garut": (-7.2232, 107.9000)
}

# --- FUNGSI HELPER: Logika Pengelompokan Bisnis ---
def group_kategori(kat):
    kat = str(kat).lower()
    if any(x in kat for x in ['bakso', 'mie', 'bakmie']): return '🍜 Mie & Bakso'
    if any(x in kat for x in ['ayam', 'lele', 'sate', 'bebek']): return '🍗 Lauk Bakar/Goreng'
    if any(x in kat for x in ['padang', 'soto', 'nasi', 'warung']): return '🍚 Nasi & Soto'
    if any(x in kat for x in ['dimsum', 'snack', 'roti', 'kue']): return '🥟 Camilan & Dimsum'
    return '🍽️ Kuliner Lainnya'

# 2. LOAD DATA (KOLOM REVIEWS DIHAPUS)
@st.cache_data
def load_data():
    file_path = "data_jabar_umkm.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
            
        df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
        
        if 'Kategori' in df.columns:
            df['Kelompok_Bisnis'] = df['Kategori'].apply(group_kategori)
        else:
            df['Kelompok_Bisnis'] = 'Lainnya'
            
        return df
    return None

df = load_data()

# 3. SIDEBAR NAVIGATION
if df is not None:
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3222/3222640.png", width=80)
        st.title("Dasboard")
        menu = st.radio(
            "Navigasi Analisis:",
            ["💎 Ringkasan Data", "📈 Visualisasi Data", "🗺️ Pemetaan UMKM Daerah Jabar", "📋 Data Mentah UMKM Daerah Jabar"]
        )
        
        st.markdown("---")
        col_wil = 'Wilayah' if 'Wilayah' in df.columns else ('Kota' if 'Kota' in df.columns else None)
        
        if col_wil:
            list_wilayah = ["Daerah Jawa Barat"] + sorted(list(KOTA_COORDS.keys()))
            selected_city = st.selectbox("📍 Fokus Wilayah:", list_wilayah)
            
            if selected_city == "Daerah Jawa Barat":
                f_df = df
            else:
                f_df = df[df[col_wil] == selected_city]
        else:
            selected_city = "Semua Data"
            f_df = df
else:
    st.error("File 'data_jabar_umkm.csv' tidak ditemukan!")
    st.stop()

# 4. KONTEN UTAMA
if menu == "💎 Ringkasan Data":
    st.title(f"📊 Dashboard Strategis: {selected_city}")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Outlet", f"{len(f_df)} Unit")
    with c2: st.metric("Avg Rating", f"{f_df['Rating'].mean():.2f} ⭐")
    with c3:
        top_sector = f_df['Kelompok_Bisnis'].mode()[0] if not f_df.empty else "N/A"
        st.metric("Sektor Terpadat", top_sector)
    with c4:
        market_potential = "Tinggi" if f_df['Rating'].mean() < 4.3 else "Menengah"
        st.metric("Potensi Profit", market_potential)

    st.markdown("---")
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.subheader("💡 Rekomendasi Peluang Buka Usaha")
        if not f_df.empty:
            counts = f_df['Kelompok_Bisnis'].value_counts()
            st.info(f"**Market Gap Detected:** Sektor **{counts.idxmin()}** memiliki kompetisi terendah.")
            st.warning(f"**Saturasi Tinggi:** Sektor **{counts.idxmax()}** sangat padat.")
        else:
            st.write("Data kosong.")

    with col_right:
        if not f_df.empty:
            fig = px.sunburst(f_df, path=['Kelompok_Bisnis', 'Kategori'], 
                              values='Rating', 
                              title="Hierarki Pasar Kuliner (% Kontribusi Rating)")
            fig.update_traces(textinfo="label+percent parent")
            st.plotly_chart(fig, use_container_width=True)

elif menu == "📈 Visualisasi Data":
    st.title("📈 Grafik Dan Rating")
    tab1, tab2 = st.tabs(["Volume Kompetisi", "Peta Kualitas"])
    with tab1:
        comp_df = f_df.groupby('Kategori').agg({'Nama': 'count', 'Rating': 'mean'}).rename(columns={'Nama': 'Total', 'Rating': 'Avg'}).reset_index()
        fig2 = px.bar(comp_df.sort_values('Total', ascending=False), x='Kategori', y='Total', color='Avg', title="Kategori vs Rating")
        st.plotly_chart(fig2, use_container_width=True)
    with tab2:
        fig3 = px.scatter(f_df, x="Rating", y="Kelompok_Bisnis", size="Rating", color="Kelompok_Bisnis", hover_name="Nama")
        st.plotly_chart(fig3, use_container_width=True)

elif menu == "🗺️ Pemetaan UMKM Daerah Jabar":
    st.title(f"📍 Peta Sebaran: {selected_city}")
    col_map, col_stat = st.columns([3, 1])
    
    with col_stat:
        st.write("**Legend:**")
        st.success("🔵 Rating > 4.0")
        st.warning("🟠 Rating <= 4.0")
        st.markdown("---")
        show_heatmap = st.checkbox("Aktifkan Heatmap")
        selected_cat = st.multiselect("Filter Kategori:", f_df['Kelompok_Bisnis'].unique(), default=f_df['Kelompok_Bisnis'].unique())

    with col_map:
        map_center = KOTA_COORDS.get(selected_city, [-6.9175, 107.6191])
        zoom_lvl = 12 if selected_city != "Seluruh Jawa Barat" else 9
        map_df = f_df[f_df['Kelompok_Bisnis'].isin(selected_cat)].dropna(subset=['lat', 'lng'])
        
        m = folium.Map(location=map_center, zoom_start=zoom_lvl, tiles="CartoDB positron")
        if not map_df.empty:
            if show_heatmap:
                HeatMap([[r['lat'], r['lng']] for i, r in map_df.iterrows()]).add_to(m)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in map_df.iterrows():
                folium.Marker([row['lat'], row['lng']], popup=f"{row['Nama']} ({row['Rating']})",
                              icon=folium.Icon(color="blue" if row['Rating'] > 4.0 else "orange")).add_to(marker_cluster)
            st_folium(m, width="100%", height=550, key=f"map_{selected_city}")

elif menu == "📋 Data Mentah UMKM Daerah Jabar":
    st.title("📋 Data Data UMKM")
    search = st.text_input("Cari Bisnis:")
    
    display_df = f_df[f_df['Nama'].str.contains(search, case=False)] if search else f_df.copy()
    
    # Membuat Index mulai dari 1
    display_df.index = range(1, len(display_df) + 1)
    
    # Menampilkan tabel data (Tombol unduh CSV telah dihapus)
    st.dataframe(display_df, use_container_width=True)

# FOOTER
st.sidebar.markdown("---")
st.sidebar.caption("© Kelompok Superman - Analisis Peluang Usaha UMKM")
