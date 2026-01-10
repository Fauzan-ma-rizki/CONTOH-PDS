import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="Tugas Besar PDS", layout="wide")

if 'last_scraping_time' not in st.session_state:
    st.session_state.last_scraping_time = None

st.title("JUDUL TUGAS BESAR: Analisis Kuliner Kota Bandung")
st.write("Fakultas Teknik dan Ilmu Komputer, Universitas Komputer Indonesia")

# Sidebar
if st.sidebar.button("Jalankan Scraping Baru"):
    # Gunakan UTC + 7 untuk WIB
    sekarang_wib = datetime.utcnow() + timedelta(hours=7)
    
    if st.session_state.last_scraping_time is None or \
       (sekarang_wib - st.session_state.last_scraping_time) > timedelta(minutes=1):
        
        with st.spinner('Scraping data asli sedang berjalan...'):
            try:
                from scrapper import scrape_gmaps
                scrape_gmaps("kuliner bandung", total_data=1000)
                st.session_state.last_scraping_time = sekarang_wib
                st.sidebar.success("Scrapping Berhasil!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        st.sidebar.warning("Tunggu 1 menit untuk scraping ulang.")

try:
    df = pd.read_csv("data_bandung.csv")
    
    # Info Waktu (Sudah WIB)
    if st.session_state.last_scraping_time:
        waktu_str = st.session_state.last_scraping_time.strftime('%H:%M:%S')
    else:
        waktu_str = "Belum ada"
        
    st.info(f"Data Terakhir Di-scrap (WIB): {waktu_str} | Total Record: {len(df)}")

    # 1. Visualisasi Data Asli
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(df, names='Kategori', title='Persentase Jenis Kuliner', hole=0.3))
    with c2:
        rating_df = df['Rating'].value_counts().reset_index().sort_values('Rating')
        rating_df.columns = ['Rating', 'Jumlah']
        fig = px.bar(rating_df, x='Rating', y='Jumlah', color='Rating', color_continuous_scale='Turbo')
        fig.update_layout(bargap=0.3, xaxis_type='category', title='Distribusi Rating Asli')
        st.plotly_chart(fig)

    # 2. GIS Popup Lengkap
    st.subheader("Geographic Information System (GIS) Bandung")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=13)
    for i, row in df.head(100).iterrows():
        html = f"""
        <div style="font-family: Arial;">
            <b>{row['Nama']}</b><br>
            ⭐ Rating: {row['Rating']}<br>
            💰 Harga: {row['Harga']}<br>
            🕒 Jam: {row['Jam']}<br>
            Status: <b style="color:{'green' if row['Status']=='Buka' else 'red'}">{row['Status']}</b>
        </div>
        """
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(html, max_width=200)).add_to(m)
    st_folium(m, width=1200, height=500)

except FileNotFoundError:
    st.warning("Data belum tersedia. Klik tombol Scraping di sidebar.")

# Resource Tabel
st.markdown("---")
st.table({
    "No.": [1, 2, 3],
    "Alamat": ["Link Live", "Source Code", "Sumber Data"],
    "Link": ["Streamlit Cloud", "GitHub", "Google Maps"]
})
