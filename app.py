import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="Big Data UMKM Jawa Barat", layout="wide")

# --- SIDEBAR NAVIGASI ---
st.sidebar.title("📊 Navigasi Big Data")

# 1. Fitur Update Data
if st.sidebar.button("🚀 Ambil 1000 Data Se-Jabar"):
    from scrapper import scrape_jabar_raya
    with st.spinner('Proses scraping 1000 data sedang berjalan (5-8 menit)...'):
        if scrape_jabar_raya(1000):
            st.success("✅ Data Berhasil Diperbarui!")
            st.rerun()

st.sidebar.markdown("---")

# --- LOGIKA DATA & FILTER ---
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # FILTER 1: Nama Kota/Wilayah (Dropdown)
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Wilayah:", list_kota)
    
    # FILTER 2: Kategori Makanan (Text Input)
    search_food = st.sidebar.text_input("🍔 Cari Jenis Kuliner:", placeholder="Contoh: Bakso, Kopi, Cafe")

    # Eksekusi Filter Gabungan
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = filtered_df[filtered_df['Kota'] == selected_city]
    if search_food:
        filtered_df = filtered_df[filtered_df['Kategori'].str.contains(search_food, case=False)]

    # --- HEADER DASHBOARD ---
    st.title(f"🚀 Dashboard Strategis UMKM")
    st.subheader(f"Analisis: {selected_city} | Kuliner: {search_food if search_food else 'Semua'}")
    st.write(f"Ditemukan **{len(filtered_df)}** titik kompetitor yang sesuai.")

    if not filtered_df.empty:
        # --- ANALISIS 3 PILAR STRATEGIS ---
        counts = filtered_df['Kategori'].value_counts()
        avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
        
        st.markdown("---")
        st.subheader("💡 Insight Peluang & Risiko")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.success(f"### ✅ Peluang Emas\n**{counts.idxmin()}**")
            st.caption(f"Persaingan terendah dengan hanya {counts.min()} kompetitor.")
        
        with c2:
            st.warning(f"### ⚠️ Peluang Sulit\n**{counts.idxmax()}**")
            st.caption(f"Pasar sangat jenuh ({counts.max()} kompetitor). Butuh inovasi besar.")
            
        with c3:
            st.error(f"### 🚩 Risiko Kualitas\n**{avg_ratings.idxmax()}**")
            st.caption(f"Ekspektasi tinggi (Avg Rating {avg_ratings.max():.1f}). Sulit jika kualitas standar.")

        # --- VISUALISASI GRAFIK ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie Chart
            fig_pie = px.pie(
                filtered_df, 
                names='Kategori', 
                title="Dominasi Pasar (Market Share)",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col2:
            # Bar Chart Rating
            avg_df = avg_ratings.reset_index()
            fig_bar = px.bar(
                avg_df, 
                x='Kategori', 
                y='Rating', 
                title="Kualitas Layanan Kompetitor (Avg Rating)",
                color='Rating',
                color_continuous_scale='RdYlGn',
                range_y=[0, 5]
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- GIS MAP DENGAN MARKER CLUSTER ---
        st.markdown("---")
        st.subheader(f"📍 Pemetaan Geografis Kompetitor")
        
        # Penentuan Center Peta
        center_lat = filtered_df['lat'].mean()
        center_lng = filtered_df['lng'].mean()
        
        m = folium.Map(location=[center_lat, center_lng], zoom_start=10 if selected_city == "Seluruh Jawa Barat" else 13)
        
        # Marker Cluster untuk performa Big Data
        marker_cluster = MarkerCluster().add_to(m)

        for _, row in filtered_df.iterrows():
            status_color = "blue" if row['Status'] == "Buka" else "red"
            popup_text = f"""
            <div style='width: 200px; font-family: Arial;'>
                <b>{row['Nama']}</b><br>
                ⭐ Rating: {row['Rating']}<br>
                🕒 Jam: {row['Jam']}<br>
                📍 Status: {row['Status']}
            </div>
            """
            folium.Marker(
                location=[row['lat'], row['lng']],
                popup=folium.Popup(popup_text, max_width=250),
                icon=folium.Icon(color=status_color, icon="utensils", prefix="fa")
            ).add_to(marker_cluster)
        
        st_folium(m, width=1300, height=550)

    else:
        st.warning(f"Tidak ada data ditemukan untuk wilayah '{selected_city}' dengan kategori '{search_food}'.")

except Exception as e:
    st.info("👋 **Selamat Datang!** Silakan klik tombol **'Ambil 1000 Data Se-Jabar'** untuk memulai analisis.")

# --- FOOTER ---
st.markdown("---")
st.caption("Aplikasi Analisis Strategis UMKM Jawa Barat © 2026")
