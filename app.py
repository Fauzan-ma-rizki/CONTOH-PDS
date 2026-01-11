import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Big Data UMKM Jawa Barat", layout="wide")

# --- SIDEBAR ---
st.sidebar.title("📊 Navigasi Big Data")
st.sidebar.info("Gunakan tombol di bawah untuk mengambil 1000 data terbaru dari berbagai kota di Jawa Barat.")

if st.sidebar.button("🚀 Ambil 1000 Data Se-Jabar"):
    from scrapper import scrape_jabar_raya
    with st.spinner('Proses scraping 1000 data sedang berjalan (estimasi 5-8 menit)...'):
        if scrape_jabar_raya(1000):
            st.success("✅ 1000 Data Berhasil Diperbarui!")
            st.rerun()

# --- LOGIKA DATA ---
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Filter Kota di Sidebar
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("Pilih Wilayah Analisis:", list_kota)
    
    if selected_city == "Seluruh Jawa Barat":
        filtered_df = df
    else:
        filtered_df = df[df['Kota'] == selected_city]

    # --- HEADER ---
    st.title(f"🚀 Dashboard Strategis UMKM: {selected_city}")
    st.markdown(f"Menganalisis total **{len(filtered_df)}** titik kompetitor kuliner.")

    if not filtered_df.empty:
        # --- HITUNG STATISTIK ---
        counts = filtered_df['Kategori'].value_counts()
        avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
        
        # --- KESIMPULAN STRATEGIS 3 PILAR ---
        st.subheader("💡 Analisis Peluang & Risiko Bisnis")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.success(f"### ✅ Peluang Emas\n**{counts.idxmin()}**")
            st.write(f"Kategori ini memiliki jumlah saingan paling sedikit ({counts.min()} toko). Peluang besar untuk menjadi market leader.")
        
        with c2:
            st.warning(f"### ⚠️ Peluang Sulit\n**{counts.idxmax()}**")
            st.write(f"Pasar sudah **JENUH** dengan {counts.max()} kompetitor. Persaingan harga di {selected_city} akan sangat berdarah-darah.")
            
        with c3:
            st.error(f"### 🚩 Risiko Kualitas\n**{avg_ratings.idxmax()}**")
            st.write(f"Ekspektasi pelanggan sangat tinggi (Avg Rating {avg_ratings.max():.1f}). Anda butuh modal besar untuk standar layanan premium.")

        # --- VISUALISASI GRAFIK ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                filtered_df, 
                names='Kategori', 
                title="Dominasi Kategori Kompetitor (Market Share)",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            avg_df = avg_ratings.reset_index()
            fig_bar = px.bar(
                avg_df, 
                x='Kategori', 
                y='Rating', 
                title="Standar Kualitas Kompetitor (Avg Rating)",
                color='Rating',
                color_continuous_scale='RdYlGn',
                range_y=[0, 5]
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- GIS MAP DENGAN MARKER CLUSTER ---
        st.markdown("---")
        st.subheader(f"📍 Pemetaan Geografis Kompetitor ({selected_city})")
        
        # Tentukan pusat peta
        center_lat = filtered_df['lat'].mean()
        center_lng = filtered_df['lng'].mean()
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=9 if selected_city == "Seluruh Jawa Barat" else 12)
        
        # Gunakan MarkerCluster agar 1000 data tidak berat saat di-render
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in filtered_df.iterrows():
            status_color = "blue" if row['Status'] == "Buka" else "red"
            folium.Marker(
                location=[row['lat'], row['lng']],
                popup=f"<b>{row['Nama']}</b><br>⭐ {row['Rating']}<br>🕒 {row['Jam']}",
                icon=folium.Icon(color=status_color, icon="utensils", prefix="fa")
            ).add_to(marker_cluster)
        
        st_folium(m, width=1300, height=550)

    else:
        st.warning("Data tidak ditemukan untuk filter ini.")

except Exception as e:
    st.info("👋 **Selamat Datang!** Data belum tersedia. Silakan klik tombol **'Ambil 1000 Data Se-Jabar'** di sidebar untuk memulai analisis big data.")

# --- FOOTER ---
st.markdown("---")
st.caption("Tugas Besar Analisis Peluang UMKM - Berbasis Real-time Google Maps Scraping")
