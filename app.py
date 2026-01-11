import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# 1. Konfigurasi Halaman & Tema
st.set_page_config(
    page_title="Sistem Informasi Strategis UMKM Jabar", 
    page_icon="🏪",
    layout="wide"
)

# --- 2. CUSTOM CSS UNTUK UI MODERN ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-bottom: 4px solid #007BFF;
    }
    .stSidebar { background-color: #ffffff; }
    h1, h2, h3 { color: #1E1E1E; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.markdown("<h1 style='text-align: center;'>📊 ANALISIS UMKM</h1>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Menu Navigasi dengan Ikon
menu = st.sidebar.radio(
    "🧭 MENU NAVIGASI",
    ["💡 Kesimpulan Strategis", "📈 Analisis Grafik", "📍 Pemetaan GIS (Peta)"],
    captions=["Insight peluang bisnis", "Data visual kompetitor", "Sebaran lokasi real-time"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ FILTER WILAYAH")

# --- 4. LOGIKA DATA ---
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    
    # Filter Wilayah
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("Pilih Kota/Kabupaten:", list_kota)

    # Tombol Scraping di Sidebar
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 PERBARUI 1000 DATA JABAR", use_container_width=True):
        from scrapper import scrape_jabar_raya
        with st.spinner('Sedang menarik data dari Google Maps...'):
            if scrape_jabar_raya(1000):
                st.success("✅ Data Berhasil Disinkronkan!")
                st.rerun()

    # Eksekusi Filter Kota
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = filtered_df[filtered_df['Kota'] == selected_city]

    # --- 5. ROUTING HALAMAN ---

    if menu == "💡 Kesimpulan Strategis":
        st.markdown(f"# 💡 Insight Strategis Bisnis: {selected_city}")
        st.write("Analisis tingkat kejenuhan pasar dan peluang kompetitif.")
        
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
            
            # Row 1: Metrics
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(label="🏆 PELUANG EMAS (MIN SAINGAN)", value=counts.idxmin(), delta="Persaingan Rendah")
            with c2:
                st.metric(label="⚠️ PASAR JENUH (MAX SAINGAN)", value=counts.idxmax(), delta="Persaingan Tinggi", delta_color="inverse")
            with c3:
                best_cat = avg_ratings.loc[avg_ratings['Rating'].idxmax()]
                st.metric(label="🚩 STANDAR KUALITAS TERTINGGI", value=best_cat['Kategori'], delta=f"{best_cat['Rating']:.1f} Stars")
            
            st.markdown("---")
            # Row 2: Detailed Insight
            st.info(f"""
            ### 📝 Rekomendasi Untuk Pengusaha:
            Berdasarkan data sebaran di **{selected_city}**, kategori **{counts.idxmin()}** memiliki hambatan masuk yang paling rendah. 
            Jika Anda ingin membuka usaha di kategori **{counts.idxmax()}**, pastikan Anda memiliki keunggulan unik (Unique Selling Point) karena pasar sudah sangat padat.
            """)
        else:
            st.warning("Data belum tersedia. Silakan klik 'Perbarui Data' di sidebar.")

    elif menu == "📈 Analisis Grafik":
        st.markdown(f"# 📈 Visualisasi Distribusi Pasar: {selected_city}")
        
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(
                    filtered_df, names='Kategori', 
                    title="<b>Dominasi Kategori Kompetitor</b>", 
                    hole=0.5,
                    color_discrete_sequence=px.colors.qualitative.Bold
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                fig_bar = px.bar(
                    avg_df, x='Kategori', y='Rating', color='Rating', 
                    title="<b>Kualitas Layanan (Rata-rata Rating)</b>", 
                    color_continuous_scale='RdYlGn',
                    text_auto='.1f'
                )
                fig_bar.update_layout(yaxis_range=[0,5])
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Data belum tersedia.")

    elif menu == "📍 Pemetaan GIS (Peta)":
        st.markdown(f"# 📍 Sebaran Geografis Kompetitor: {selected_city}")
        st.write("Warna Biru: Buka | Warna Merah: Tutup")
        
        if not filtered_df.empty:
            map_center = [filtered_df['lat'].mean(), filtered_df['lng'].mean()]
            m = folium.Map(location=map_center, zoom_start=12, tiles="cartodbpositron")
            
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in filtered_df.iterrows():
                # Ikon Keren: Menggunakan FontAwesome utensils (sendok garpu)
                color = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    location=[row['lat'], row['lng']],
                    popup=folium.Popup(f"<b>{row['Nama']}</b><br>Rating: ⭐{row['Rating']}<br>Status: {row['Status']}", max_width=300),
                    icon=folium.Icon(color=color, icon="utensils", prefix="fa")
                ).add_to(marker_cluster)
            
            st_folium(m, width=1300, height=600)
        else:
            st.warning("Data belum tersedia.")

except Exception as e:
    st.info("👋 **Selamat Datang!** Database belum terdeteksi. Silakan klik tombol **'PERBARUI 1000 DATA JABAR'** di sidebar untuk memulai scraping data real-time.")

st.sidebar.markdown("---")
st.sidebar.caption("Sistem Intelijen Bisnis UMKM Jabar © 2026")
