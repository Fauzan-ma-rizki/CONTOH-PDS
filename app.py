import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="UMKM Strategy Dashboard Jabar", layout="wide")

# CSS Fix untuk Streamlit Cloud
st.markdown("""
    <style>
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 Business Intelligence")
menu = st.sidebar.radio(
    "Pilih Menu Visualisasi:",
    ["💡 Kesimpulan Strategis", "📊 Analisis Grafik", "📍 Pemetaan GIS (Peta)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter & Kontrol")

try:
    df = pd.read_csv("data_jabar_umkm.csv")
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("📍 Pilih Wilayah:", list_kota)
    search_food = st.sidebar.text_input("🍔 Cari Kuliner Spesifik:", placeholder="Contoh: Kopi")

    if st.sidebar.button("🔄 Perbarui 1000 Data Baru"):
        from scrapper import scrape_jabar_raya
        with st.spinner('Scraping 1000 data se-Jawa Barat...'):
            if scrape_jabar_raya(1000): st.rerun()

    # Filter Data
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = filtered_df[filtered_df['Kota'] == selected_city]
    if search_food:
        filtered_df = filtered_df[filtered_df['Kategori'].str.contains(search_food, case=False)]

    # --- HALAMAN 1: KESIMPULAN ---
    if menu == "💡 Kesimpulan Strategis":
        st.title("💡 Analisis Peluang & Risiko Bisnis")
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Peluang Emas (Saingan Sedikit)", counts.idxmin(), f"{counts.min()} Toko")
            c2.metric("Peluang Sulit (Pasar Jenuh)", counts.idxmax(), f"{counts.max()} Toko", delta_color="inverse")
            c3.metric("Risiko Kualitas (Rating Tertinggi)", avg_ratings.idxmax(), f"{avg_ratings.max():.1f} ⭐")
            
            st.markdown("---")
            st.success(f"### Kesimpulan Usaha di {selected_city}")
            st.write(f"Berdasarkan analisis Big Data, kategori **{counts.idxmin()}** adalah pilihan paling rasional karena minim kompetitor. Sebaliknya, hindari kategori **{counts.idxmax()}** kecuali Anda memiliki modal besar untuk promosi.")
        else:
            st.warning("Data kosong. Silakan perbarui data di sidebar.")

    # --- HALAMAN 2: GRAFIK ---
    elif menu == "📊 Analisis Grafik":
        st.title("📊 Distribusi Pasar & Kualitas")
        if not filtered_df.empty:
            t1, t2 = st.tabs(["📈 Market Share", "⭐ Peringkat Kualitas"])
            with t1:
                st.plotly_chart(px.pie(filtered_df, names='Kategori', hole=0.4, title="Dominasi Kategori"), use_container_width=True)
            with t2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                st.plotly_chart(px.bar(avg_df, x='Kategori', y='Rating', color='Rating', title="Avg Rating per Kategori", range_y=[0,5]), use_container_width=True)

    # --- HALAMAN 3: PETA ---
    elif menu == "📍 Pemetaan GIS (Peta)":
        st.title("📍 Sebaran Geografis Kompetitor")
        if not filtered_df.empty:
            m = folium.Map(location=[filtered_df['lat'].mean(), filtered_df['lng'].mean()], zoom_start=9)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in filtered_df.iterrows():
                folium.Marker(
                    location=[row['lat'], row['lng']],
                    popup=f"{row['Nama']} | ⭐{row['Rating']}",
                    icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red", icon="info-sign")
                ).add_to(marker_cluster)
            st_folium(m, width=1300, height=600)

except Exception as e:
    st.info("👋 Selamat Datang! Klik 'Perbarui 1000 Data' di sidebar untuk memulai.")
