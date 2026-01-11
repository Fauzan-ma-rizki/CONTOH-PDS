import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. Konfigurasi Halaman (Ikon & Judul Tab)
st.set_page_config(
    page_title="Analisis UMKM Jabar", 
    page_icon="📊", 
    layout="wide"
)

# 2. Sidebar Navigation dengan Ikon Emoji
st.sidebar.markdown("### 🧭 Navigasi Utama")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    ["💡 Kesimpulan Strategis", "📊 Analisis Grafik", "📍 Pemetaan GIS"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Manajemen Data")

# Tombol Scraping dengan warna yang menonjol secara natural
if st.sidebar.button("🚀 Ambil 1000 Data Se-Jabar", use_container_width=True):
    from scrapper import scrape_jabar_raya
    with st.spinner('Menghubungkan ke Google Maps...'):
        if scrape_jabar_raya(1000):
            st.success("Database Berhasil Diperbarui!")
            st.rerun()

# 3. Memastikan File Data Ada
if os.path.exists("data_jabar_umkm.csv"):
    df = pd.read_csv("data_jabar_umkm.csv")
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    
    # Filter Wilayah yang lebih elegan
    st.sidebar.markdown("---")
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Filter Wilayah:", list_kota)
    
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = df[df['Kota'] == selected_city]

    # --- KONTEN HALAMAN ---

    if menu == "💡 Kesimpulan Strategis":
        st.markdown(f"# 💡 Insight Bisnis: {selected_city}")
        st.caption("Analisis otomatis peluang pasar berdasarkan kepadatan kompetitor dan kualitas layanan.")
        
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            # Layout Metrik dalam Kontainer Putih
            with st.container():
                c1, c2, c3 = st.columns(3)
                c1.metric("✅ Peluang Emas", counts.idxmin(), help="Kategori dengan jumlah saingan paling sedikit.")
                c2.metric("⚠️ Pasar Jenuh", counts.idxmax(), help="Kategori dengan jumlah saingan terbanyak.")
                c3.metric("🚩 Standar Kualitas", f"{avg_ratings.max():.1f} ⭐", help="Rating rata-rata tertinggi di wilayah ini.")
            
            st.markdown("---")
            
            # Kolom untuk Rekomendasi
            col_rec, col_info = st.columns([2, 1])
            with col_rec:
                st.subheader("📌 Rekomendasi Strategis")
                st.write(f"""
                Berdasarkan data terbaru, kategori **{counts.idxmin()}** menunjukkan celah pasar yang sangat besar 
                di {selected_city}. Membuka usaha di sektor ini memiliki risiko persaingan harga yang lebih rendah 
                dibandingkan sektor **{counts.idxmax()}**.
                """)
            with col_info:
                st.info("**Tips:** Gunakan peta GIS untuk mencari titik koordinat yang masih kosong dari marker kompetitor.")
        else:
            st.warning("Data tidak ditemukan.")

    elif menu == "📊 Analisis Grafik":
        st.markdown(f"# 📊 Visualisasi Data: {selected_city}")
        
        if not filtered_df.empty:
            # Menggunakan Tab untuk merapikan grafik
            tab1, tab2 = st.tabs(["📈 Distribusi Pasar", "⭐ Kualitas Layanan"])
            
            with tab1:
                fig_pie = px.pie(
                    filtered_df, names='Kategori', hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    title="Market Share per Kategori"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with tab2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                fig_bar = px.bar(
                    avg_df, x='Kategori', y='Rating', color='Rating',
                    color_continuous_scale='RdYlGn', range_y=[0,5],
                    title="Peringkat Kepuasan Pelanggan (Rating)",
                    text_auto='.1f'
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    elif menu == "📍 Pemetaan GIS":
        st.markdown(f"# 📍 Sebaran Lokasi: {selected_city}")
        
        if not filtered_df.empty:
            with st.expander("ℹ️ Keterangan Marker"):
                st.write("🔵 **Biru**: Toko berstatus BUKA | 🔴 **Merah**: Toko berstatus TUTUP")
            
            m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=12)
            marker_cluster = MarkerCluster().add_to(m)
            
            for _, row in filtered_df.iterrows():
                warna = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    [row['lat'], row['lng']],
                    popup=f"<b>{row['Nama']}</b><br>Rating: {row['Rating']}",
                    icon=folium.Icon(color=warna, icon="shopping-cart", prefix="fa")
                ).add_to(marker_cluster)
            
            st_folium(m, width=1300, height=600)

else:
    # Desain Landing Page yang Bersih
    st.title("📊 Platform Analisis UMKM Jabar")
    st.markdown("---")
    c_a, c_b = st.columns([1, 2])
    with c_a:
        st.image("https://cdn-icons-png.flaticon.com/512/3168/3168190.png", use_container_width=True)
    with c_b:
        st.subheader("Database Belum Terdeteksi")
        st.write("""
        Selamat datang di sistem pendukung keputusan UMKM. Aplikasi ini menggunakan data real-time 
        dari Google Maps untuk memetakan peluang usaha di wilayah Jawa Barat.
        
        **Langkah untuk memulai:**
        1. Klik tombol **Ambil 1000 Data Se-Jabar** di sidebar.
        2. Tunggu proses scraping selesai.
        3. Dashboard akan otomatis muncul setelah data siap.
        """)

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Business Intelligence UMKM")
