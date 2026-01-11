import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

# Sidebar
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung atau Bakso")

if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner('Mengambil data asli dari Google Maps...'):
        sukses = scrape_gmaps("kuliner jawa barat", total_data=60)
        if sukses:
            st.success("Data berhasil diperbarui!")
            st.rerun()

# Logic Utama
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    if user_query:
        mask = df['Kota'].str.contains(user_query, case=False) if search_type == "Kota/Kabupaten" else df['Kategori'].str.contains(user_query, case=False)
        filtered_df = df[mask]
        target_col = 'Kategori' if search_type == "Kota/Kabupaten" else 'Kota'
    else:
        filtered_df = df
        target_col = 'Kategori'

    st.title(f"🚀 Analisis Strategis UMKM: {user_query if user_query else 'Jawa Barat'}")

    # --- KESIMPULAN OTOMATIS ---
    st.info("### 💡 Kesimpulan Strategis Berbasis Data")
    if not filtered_df.empty:
        counts = filtered_df[target_col].value_counts()
        kompetitor_terbanyak = counts.idxmax()
        kompetitor_terkecil = counts.idxmin()
        rating_tertinggi = filtered_df.groupby(target_col)['Rating'].mean().idxmax()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Kompetitor Dominan", kompetitor_terbanyak)
        c2.metric("Peluang Emas", kompetitor_terkecil)
        c3.metric("Kualitas Tertinggi", rating_tertinggi)
        
        st.write(f"👉 **Analisis:** Kategori **{kompetitor_terbanyak}** sudah sangat jenuh di area ini. Jika ingin membuka usaha baru, sektor **{kompetitor_terkecil}** menawarkan peluang karena tingkat persaingan paling rendah.")
    else:
        st.warning("Data tidak ditemukan. Silakan lakukan 'Perbarui Data'.")

    # --- VISUALISASI ---
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(filtered_df, names=target_col, title="Sebaran Kategori Kuliner", hole=0.4), use_container_width=True)
    with col2:
        if not filtered_df.empty:
            avg_rate = filtered_df.groupby(target_col)['Rating'].mean().reset_index()
            st.plotly_chart(px.bar(avg_rate, x=target_col, y='Rating', color='Rating', title="Kepuasan Pelanggan (Avg Rating)"), use_container_width=True)

    # --- GIS MAP ---
    st.subheader("📍 Peta Lokasi & Status Toko")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for _, row in filtered_df.head(40).iterrows():
        warna = "blue" if row['Status'] == "Buka" else "red"
        popup_html = f"""
        <div style='font-family: Arial; width: 200px;'>
            <b>{row['Nama']}</b><br>
            ⭐ Rating: {row['Rating']}<br>
            🕒 Jam: {row['Jam']}<br>
            📍 Status: {row['Status']}
        </div>
        """
        folium.Marker(
            [row['lat'], row['lng']], 
            popup=folium.Popup(popup_html, max_width=250),
            icon=folium.Icon(color=warna, icon="utensils", prefix="fa")
        ).add_to(m)
    st_folium(m, width=1300, height=500)

except FileNotFoundError:
    st.warning("Data belum tersedia. Klik 'Perbarui Data' di sidebar.")
