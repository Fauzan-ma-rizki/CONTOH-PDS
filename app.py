import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. Konfigurasi Halaman
st.set_page_config(
    page_title="Strategic UMKM Advisor - Jabar", 
    page_icon="🎯", 
    layout="wide"
)

# Fungsi Pengelompokan (Hanya untuk keperluan visualisasi grafik)
def group_kategori(kat):
    kat = str(kat).lower()
    if 'kopi' in kat or 'cafe' in kat: return 'Kopi & Cafe'
    if 'ayam' in kat or 'pecel' in kat or 'sate' in kat or 'sunda' in kat or 'padang' in kat: return 'Makanan Berat'
    if 'roti' in kat or 'martabak' in kat: return 'Roti & Kue'
    if 'jus' in kat or 'minuman' in kat: return 'Minuman & Jus'
    if 'bakso' in kat or 'mie' in kat or 'warmindo' in kat: return 'Mie & Bakso'
    if 'seblak' in kat: return 'Seblak & Camilan'
    return 'Lainnya'

# 2. Sidebar Navigation
st.sidebar.markdown("### Analisis Peluang Usaha UMKM")
menu = st.sidebar.radio(
    "Menu Utama:",
    ["💡 Rekomendasi Peluang", "📊 Analisis Visual", "📍 Peta GIS"]
)

st.sidebar.markdown("---")

# Tombol Sinkronisasi Data
if st.sidebar.button("🚀 Scrape Data Real-Time", use_container_width=True):
    from scrapper import scrape_jabar_raya
    with st.spinner('Mengambil data 1000 UMKM se-Jawa Barat...'):
        if scrape_jabar_raya(1000):
            st.success("Database Terupdate!")
            st.rerun()

# 3. Logika Loading & Processing Data
if os.path.exists("data_jabar_umkm.csv"):
    df = pd.read_csv("data_jabar_umkm.csv")
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    df['Kelompok_Bisnis'] = df['Kategori'].apply(group_kategori)
    
    st.sidebar.markdown("---")
    col_wil = 'Wilayah' if 'Wilayah' in df.columns else 'Kota'
    list_wilayah = ["Seluruh Jawa Barat"] + sorted(df[col_wil].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Lokasi Analisis:", list_wilayah)
    
    filtered_df = df if selected_city == "Seluruh Jawa Barat" else df[df[col_wil] == selected_city]

    # --- KONTEN HALAMAN ---

    if menu == "💡 Rekomendasi Peluang":
        st.markdown(f"# 🎯 Rekomendasi Peluang Usaha: {selected_city}")
        st.write("Analisis berbasis data kompetisi spesifik di lapangan.")
        
        if not filtered_df.empty:
            # Hitung berdasarkan Kategori Asli (Spesifik)
            counts_spesifik = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            # --- TAMPILAN 3 REKOMENDASI UTAMA ---
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.success("### ✅ Peluang Emas")
                st.subheader(counts_spesifik.idxmin())
                st.write(f"Hanya ada **{counts_spesifik.min()}** kompetitor di wilayah ini. Sangat disarankan untuk penetrasi pasar segera.")
            
            with c2:
                st.warning("### ⚠️ Pasar Jenuh")
                st.subheader(counts_spesifik.idxmax())
                st.write(f"Sudah ada **{counts_spesifik.max()}** toko sejenis. Persaingan harga sangat ketat di sektor ini.")
            
            with c3:
                best_rating_cat = avg_ratings.idxmax()
                st.error("### 🚩 Standar Kualitas")
                st.subheader(best_rating_cat)
                st.write(f"Rata-rata rating **{avg_ratings.max():.1f} ⭐**. Jika Anda masuk ke sini, standar pelayanan harus sangat tinggi.")

            st.markdown("---")
            
            # --- TABEL REKOMENDASI TAMBAHAN ---
            st.subheader("📋 Peringkat Peluang Usaha (Dari Terendah Saingan)")
            res_df = counts_spesifik.reset_index()
            res_df.columns = ['Jenis Usaha', 'Jumlah Kompetitor']
            
            def get_status(count):
                if count <= res_df['Jumlah Kompetitor'].quantile(0.33): return "⭐⭐⭐ Sangat Tinggi"
                if count <= res_df['Jumlah Kompetitor'].quantile(0.66): return "⭐⭐ Menengah"
                return "⭐ Rendah (Jenuh)"
            
            res_df['Potensi Keberhasilan'] = res_df['Jumlah Kompetitor'].apply(get_status)
            st.table(res_df.head(5))

    elif menu == "📊 Analisis Visual":
        st.markdown(f"# 📊 Perbandingan Industri: {selected_city}")
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(filtered_df, names='Kelompok_Bisnis', title="Dominasi Sektor Kuliner", hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                avg_df = filtered_df.groupby('Kelompok_Bisnis')['Rating'].mean().reset_index()
                fig_bar = px.bar(avg_df, x='Kelompok_Bisnis', y='Rating', color='Rating', title="Kualitas Layanan per Sektor", range_y=[0,5], text_auto='.1f')
                st.plotly_chart(fig_bar, use_container_width=True)

    elif menu == "📍 Peta GIS":
        st.markdown(f"# 📍 Sebaran Lokasi Kompetitor: {selected_city}")
        if not filtered_df.empty:
            m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=11)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in filtered_df.iterrows():
                warna = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    [row['lat'], row['lng']], 
                    popup=f"<b>{row['Nama']}</b><br>Kategori: {row['Kategori']}<br>Rating: {row['Rating']}",
                    icon=folium.Icon(color=warna, icon="cutlery", prefix="fa")
                ).add_to(marker_cluster)
            st_folium(m, width=1300, height=600)

else:
    st.title("📊 Strategic Advisor UMKM Jawa Barat")
    st.info("Database belum tersedia. Silakan klik tombol 'Scrape Data Real-Time' di sidebar untuk memulai.")

