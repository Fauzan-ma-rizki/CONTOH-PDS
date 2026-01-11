import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. Konfigurasi Halaman (Harus di baris paling atas setelah import)
st.set_page_config(page_title="Analisis Strategis UMKM Jabar", layout="wide")

# 2. CSS agar UI Menarik & Terlihat Profesional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        border-left: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar Navigation
st.sidebar.title("📊 Dashboard Navigasi")
menu = st.sidebar.radio(
    "Pilih Menu:",
    ["💡 Kesimpulan Strategis", "📈 Analisis Grafik", "📍 Pemetaan GIS (Peta)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Kontrol Data")

# Tombol Scraping
if st.sidebar.button("🚀 Ambil 1000 Data Se-Jabar"):
    from scrapper import scrape_jabar_raya
    with st.spinner('Sedang mengambil data...'):
        if scrape_jabar_raya(1000):
            st.success("Data Berhasil Diperbarui!")
            st.rerun()

# 4. Logika Loading Data
if os.path.exists("data_jabar_umkm.csv"):
    df = pd.read_csv("data_jabar_umkm.csv")
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    
    # Filter Kota
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Wilayah:", list_kota)
    
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = df[df['Kota'] == selected_city]

    # --- TAMPILAN BERDASARKAN MENU ---
    
    if menu == "💡 Kesimpulan Strategis":
        st.title(f"💡 Strategi Bisnis: {selected_city}")
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("✅ Peluang Emas", counts.idxmin(), f"{counts.min()} Toko")
            c2.metric("⚠️ Peluang Sulit", counts.idxmax(), f"{counts.max()} Toko", delta_color="inverse")
            c3.metric("🚩 Risiko Kualitas", avg_ratings.idxmax(), f"{avg_ratings.max():.1f} ⭐")
            
            st.info(f"Rekomendasi: Sektor **{counts.idxmin()}** adalah peluang terbaik di {selected_city}.")
        else:
            st.warning("Data untuk wilayah ini kosong.")

    elif menu == "📈 Analisis Grafik":
        st.title("📈 Distribusi Pasar & Kualitas")
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(px.pie(filtered_df, names='Kategori', title="Dominasi Kategori", hole=0.4), use_container_width=True)
        with col2:
            avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
            st.plotly_chart(px.bar(avg_df, x='Kategori', y='Rating', color='Rating', title="Avg Rating", range_y=[0,5]), use_container_width=True)

    elif menu == "📍 Pemetaan GIS (Peta)":
        st.title("📍 Pemetaan Lokasi Kompetitor")
        m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=11)
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in filtered_df.iterrows():
            folium.Marker(
                [row['lat'], row['lng']],
                popup=row['Nama'],
                icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red", icon="utensils", prefix="fa")
            ).add_to(marker_cluster)
        st_folium(m, width=1300, height=600)

else:
    # UI Tampilan Awal jika CSV Belum Ada
    st.title("🏪 Selamat Datang di Dashboard UMKM Jabar")
    st.image("https://cdn-icons-png.flaticon.com/512/3168/3168190.png", width=150)
    st.warning("Data belum tersedia di server.")
    st.info("Silakan klik tombol **'Ambil 1000 Data Se-Jabar'** di sebelah kiri untuk memulai proses scraping.")
