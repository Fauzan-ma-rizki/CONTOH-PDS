import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

# Database koordinat untuk memindahkan peta otomatis
city_coords = {
    "Bandung": [-6.9175, 107.6191],
    "Bekasi": [-6.2383, 106.9756],
    "Bogor": [-6.5971, 106.8060],
    "Depok": [-6.4025, 106.7942],
    "Cirebon": [-6.7320, 108.5523],
    "Sukabumi": [-6.9277, 106.9300]
}

# Sidebar
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", value="Bandung")

if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner(f'Mengambil data kuliner di {user_query}...'):
        # Kirim user_query sebagai parameter kota ke scraper
        sukses = scrape_gmaps("kuliner", city=user_query, total_data=40)
        if sukses:
            st.success(f"Data {user_query} Berhasil Diperbarui!")
            st.rerun()

# Logic Utama
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Filter data agar hanya menampilkan yang relevan dengan pencarian
    if user_query:
        mask = df['Kota'].str.contains(user_query, case=False) if search_type == "Kota/Kabupaten" else df['Kategori'].str.contains(user_query, case=False)
        filtered_df = df[mask]
    else:
        filtered_df = df

    st.title(f"🚀 Analisis Strategis UMKM: {user_query}")

    # --- KESIMPULAN OTOMATIS ---
    st.info("### 💡 Kesimpulan Strategis Berbasis Data")
    if not filtered_df.empty:
        # Penentuan target kolom untuk analisis
        target_col = 'Kategori' if search_type == "Kota/Kabupaten" else 'Kota'
        counts = filtered_df[target_col].value_counts()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Kompetitor Dominan", counts.idxmax())
        c2.metric("Peluang Emas", counts.idxmin())
        c3.metric("Rating Tertinggi", filtered_df.groupby(target_col)['Rating'].mean().idxmax())
    
    # --- GIS MAP (SINKRON DENGAN KOTA) ---
    st.subheader(f"📍 Sebaran Kuliner di {user_query}")
    
    # Tentukan titik tengah peta berdasarkan kota yang dicari
    map_center = city_coords.get(user_query, [-6.9175, 107.6191])
    
    m = folium.Map(location=map_center, zoom_start=13)
    
    for _, row in filtered_df.iterrows():
        warna = "blue" if row['Status'] == "Buka" else "red"
        folium.Marker(
            [row['lat'], row['lng']], 
            popup=f"<b>{row['Nama']}</b><br>⭐ {row['Rating']}<br>🕒 {row['Jam']}",
            icon=folium.Icon(color=warna, icon="utensils", prefix="fa")
        ).add_to(m)
    
    st_folium(m, width=1300, height=500)

    # Tabel Data
    with st.expander("Lihat Detail Data Mentah"):
        st.dataframe(filtered_df)

except FileNotFoundError:
    st.warning("Data belum tersedia. Klik 'Perbarui Data' di sidebar untuk mencari.")
