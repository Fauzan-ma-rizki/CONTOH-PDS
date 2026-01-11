import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Dashboard UMKM Jabar", layout="wide")

# 2. Sidebar Navigation
st.sidebar.title("Menu Navigasi")
menu = st.sidebar.radio(
    "Pilih Tampilan:",
    ["💡 Kesimpulan Strategis", "📊 Analisis Grafik", "📍 Pemetaan Peta (GIS)"]
)

st.sidebar.markdown("---")

# 3. Fungsi Scraping di Sidebar
if st.sidebar.button("🚀 Ambil 1000 Data Se-Jabar"):
    from scrapper import scrape_jabar_raya
    with st.spinner('Sedang memproses data... Mohon tunggu.'):
        if scrape_jabar_raya(1000):
            st.success("Data Berhasil Diperbarui!")
            st.rerun()

# 4. Logika Utama Data
if os.path.exists("data_jabar_umkm.csv"):
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Memastikan Rating adalah angka
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    
    # Filter Kota
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("Pilih Wilayah:", list_kota)
    
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = df[df['Kota'] == selected_city]

    # --- KONTEN HALAMAN ---

    if menu == "💡 Kesimpulan Strategis":
        st.title(f"💡 Kesimpulan Strategis: {selected_city}")
        
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            # Tampilan Metrik Sederhana
            col1, col2, col3 = st.columns(3)
            col1.metric("Peluang Emas", counts.idxmin(), f"{counts.min()} Toko")
            col2.metric("Pasar Jenuh", counts.idxmax(), f"{counts.max()} Toko")
            col3.metric("Rating Tertinggi", avg_ratings.idxmax(), f"{avg_ratings.max():.1f} Bintang")
            
            st.markdown("---")
            st.write(f"### Rekomendasi Bisnis")
            st.write(f"Berdasarkan data, sektor **{counts.idxmin()}** memiliki persaingan paling rendah di {selected_city}. Ini adalah peluang bagus untuk membuka usaha baru.")
        else:
            st.warning("Data kosong untuk wilayah ini.")

    elif menu == "📊 Analisis Grafik":
        st.title(f"📊 Grafik Analisis: {selected_city}")
        
        if not filtered_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                fig_pie = px.pie(filtered_df, names='Kategori', title="Dominasi Kategori Kuliner")
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                fig_bar = px.bar(avg_df, x='Kategori', y='Rating', color='Rating', title="Rata-rata Rating", range_y=[0,5])
                st.plotly_chart(fig_bar, use_container_width=True)

    elif menu == "📍 Pemetaan Peta (GIS)":
        st.title(f"📍 Lokasi Kompetitor: {selected_city}")
        
        if not filtered_df.empty:
            # Titik tengah peta
            m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=11)
            marker_cluster = MarkerCluster().add_to(m)
            
            for _, row in filtered_df.iterrows():
                # Warna biru untuk buka, merah untuk tutup
                warna = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    [row['lat'], row['lng']],
                    popup=f"{row['Nama']} (Rating: {row['Rating']})",
                    icon=folium.Icon(color=warna, icon="info-sign")
                ).add_to(marker_cluster)
            
            st_folium(m, width=1300, height=600)

else:
    # Tampilan jika file data belum ada
    st.title("Selamat Datang di Dashboard UMKM")
    st.info("Data belum tersedia. Silakan klik tombol **'Ambil 1000 Data Se-Jabar'** pada menu di samping kiri.")
