import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Pengaturan halaman
st.set_page_config(page_title="UMKM Strategy Dashboard", layout="wide")

# --- CUSTOM CSS UNTUK TAMPILAN MENARIK ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_stdio=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Business Intelligence")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3168/3168190.png", width=100) # Ikon UMKM

menu = st.sidebar.radio(
    "Pilih Menu Visualisasi:",
    ["💡 Kesimpulan Strategis", "📊 Analisis Grafik", "📍 Pemetaan GIS (Peta)"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Data")

try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Filter Wilayah & Makanan
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Wilayah:", list_kota)
    search_food = st.sidebar.text_input("🍔 Cari Kategori Kuliner:", placeholder="Contoh: Kopi, Bakso")

    # Tombol Update di paling bawah sidebar
    if st.sidebar.button("🔄 Perbarui 1000 Data Baru"):
        from scrapper import scrape_jabar_raya
        with st.spinner('Scraping 1000 data...'):
            scrape_jabar_raya(1000)
            st.rerun()

    # Logika Filtering
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = filtered_df[filtered_df['Kota'] == selected_city]
    if search_food:
        filtered_df = filtered_df[filtered_df['Kategori'].str.contains(search_food, case=False)]

    # --- ROUTING HALAMAN BERDASARKAN MENU SIDEBAR ---

    if menu == "💡 Kesimpulan Strategis":
        st.title("💡 Kesimpulan Strategis Buka Usaha")
        st.markdown(f"Analisis peluang bisnis untuk wilayah **{selected_city}**")
        
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            # Kartu Metrik Modern
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peluang Emas (Sepi Saingan)", counts.idxmin(), f"{counts.min()} Kompetitor")
            with col2:
                st.metric("Peluang Sulit (Pasar Jenuh)", counts.idxmax(), f"{counts.max()} Kompetitor", delta_color="inverse")
            with col3:
                st.metric("Risiko Kualitas (Rating Tinggi)", avg_ratings.idxmax(), f"{avg_ratings.max():.1f} ⭐")
            
            st.markdown("---")
            st.info(f"👉 **Saran Eksekutif:** Berdasarkan data, sektor **{counts.idxmin()}** adalah pilihan terbaik untuk investasi baru karena minimnya persaingan di {selected_city}.")
        else:
            st.warning("Data tidak tersedia untuk filter ini.")

    elif menu == "📊 Analisis Grafik":
        st.title("📊 Analisis Distribusi & Kualitas Pasar")
        
        if not filtered_df.empty:
            tab1, tab2 = st.tabs(["📈 Market Share (Pie)", "⭐ Quality Ranking (Bar)"])
            
            with tab1:
                fig_pie = px.pie(filtered_df, names='Kategori', hole=0.4, 
                                 title="Dominasi Kategori Kompetitor",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with tab2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                fig_bar = px.bar(avg_df, x='Kategori', y='Rating', color='Rating',
                                 title="Peringkat Kepuasan Pelanggan",
                                 color_continuous_scale='RdYlGn', range_y=[0,5])
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Silakan perbarui data atau ubah filter.")

    elif menu == "📍 Pemetaan GIS (Peta)":
        st.title("📍 Pemetaan Geografis Kompetitor")
        st.markdown("Klik pada *cluster* angka untuk melihat detail lokasi.")
        
        if not filtered_df.empty:
            center_lat = filtered_df['lat'].mean()
            center_lng = filtered_df['lng'].mean()
            m = folium.Map(location=[center_lat, center_lng], zoom_start=11)
            
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in filtered_df.iterrows():
                color = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    location=[row['lat'], row['lng']],
                    popup=f"<b>{row['Nama']}</b><br>Rating: {row['Rating']}<br>Status: {row['Status']}",
                    icon=folium.Icon(color=color, icon="shopping-cart", prefix="fa")
                ).add_to(marker_cluster)
            
            st_folium(m, width=1300, height=600)
        else:
            st.warning("Peta tidak dapat dimuat tanpa data.")

except Exception as e:
    st.info("👋 **Selamat Datang!** Silakan tekan tombol **Perbarui 1000 Data** di sidebar untuk memulai.")
