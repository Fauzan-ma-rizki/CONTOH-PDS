import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Pengaturan halaman
st.set_page_config(page_title="UMKM Strategy Dashboard", layout="wide")

# --- CUSTOM CSS UNTUK TAMPILAN MENARIK ---
# Perbaikan: Mengganti unsafe_allow_stdio menjadi unsafe_allow_html
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
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Business Intelligence")

menu = st.sidebar.radio(
    "Pilih Menu Visualisasi:",
    ["💡 Kesimpulan Strategis", "📊 Analisis Grafik", "📍 Pemetaan GIS (Peta)"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Data")

try:
    # Membaca data
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Filter Wilayah & Makanan
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Wilayah:", list_kota)
    search_food = st.sidebar.text_input("🍔 Cari Kategori Kuliner:", placeholder="Contoh: Kopi, Bakso")

    # Tombol Update
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

    # --- ROUTING HALAMAN ---

    if menu == "💡 Kesimpulan Strategis":
        st.title("💡 Kesimpulan Strategis Buka Usaha")
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Peluang Emas (Sepi Saingan)", counts.idxmin(), f"{counts.min()} Toko")
            with col2:
                st.metric("Peluang Sulit (Pasar Jenuh)", counts.idxmax(), f"{counts.max()} Toko", delta_color="inverse")
            with col3:
                st.metric("Risiko Kualitas (Rating Tinggi)", avg_ratings.idxmax(), f"{avg_ratings.max():.1f} ⭐")
            
            st.info(f"👉 **Saran Eksekutif:** Berdasarkan data di {selected_city}, sektor **{counts.idxmin()}** adalah pilihan terbaik.")
        else:
            st.warning("Data tidak tersedia.")

    elif menu == "📊 Analisis Grafik":
        st.title("📊 Analisis Distribusi & Kualitas")
        if not filtered_df.empty:
            tab1, tab2 = st.tabs(["📈 Market Share", "⭐ Quality Ranking"])
            with tab1:
                st.plotly_chart(px.pie(filtered_df, names='Kategori', hole=0.4), use_container_width=True)
            with tab2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                st.plotly_chart(px.bar(avg_df, x='Kategori', y='Rating', color='Rating', range_y=[0,5]), use_container_width=True)

    elif menu == "📍 Pemetaan GIS (Peta)":
        st.title("📍 Pemetaan Geografis Kompetitor")
        if not filtered_df.empty:
            m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=11)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in filtered_df.iterrows():
                folium.Marker(
                    location=[row['lat'], row['lng']],
                    popup=row['Nama'],
                    icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red")
                ).add_to(marker_cluster)
            st_folium(m, width=1300, height=600)

except Exception as e:
    st.info("👋 Silakan klik 'Perbarui Data' di sidebar untuk memulai analisis.")
