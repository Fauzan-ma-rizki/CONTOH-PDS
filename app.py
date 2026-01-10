import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import time
from datetime import datetime, timedelta

# Judul dan Header
st.set_page_config(page_title="Tugas Besar PDS", layout="wide")

if 'last_scraping_time' not in st.session_state:
    st.session_state.last_scraping_time = None

st.title("JUDUL TUGAS BESAR: Analisis Kuliner Kota Bandung")

# Sidebar
st.sidebar.header("Kontrol Data")
if st.sidebar.button("Jalankan Scraping Baru"):
    sekarang = datetime.now()
    if st.session_state.last_scraping_time is None or \
       (sekarang - st.session_state.last_scraping_time) > timedelta(minutes=1):
        
        with st.spinner('Proses scraping data sedang berjalan...'):
            try:
                from scrapper import scrape_gmaps
                scrape_gmaps("kuliner bandung", total_data=50) 
                st.session_state.last_scraping_time = sekarang
                st.sidebar.success("Scrapping Berhasil!")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Error: {e}")
    else:
        sisa = 60 - (sekarang - st.session_state.last_scraping_time).seconds
        st.sidebar.warning(f"Tunggu {sisa} detik lagi.")

try:
    df = pd.read_csv("data_bandung.csv")
    
    # Tampilan Informasi
    last_time = st.session_state.last_scraping_time.strftime('%H:%M:%S') if st.session_state.last_scraping_time else "Belum ada"
    st.info(f"Data Terakhir Di-scrap: {last_time} | Total Record: {len(df)}")

    # 1. Visualisasi
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df, names='Kategori', title='Persentase Jenis Kuliner', hole=0.3))

    with col2:
        # Visualisasi Rating Asli (Tidak Dempet)
        rating_counts = df['Rating'].value_counts().reset_index().sort_values('Rating')
        rating_counts.columns = ['Rating', 'Jumlah']
        
        fig2 = px.bar(rating_counts, x='Rating', y='Jumlah', color='Rating', 
                      color_continuous_scale='Turbo', title='Distribusi Rating', text='Jumlah')
        fig2.update_layout(bargap=0.3, xaxis_type='category')
        st.plotly_chart(fig2)

    # 2. GIS dengan Info Lengkap
    st.subheader("Geographic Information System (GIS) Bandung")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=13)
    
    for i, row in df.head(100).iterrows():
        html_popup = f"""
        <div style="font-family: Arial; width: 200px;">
            <h4 style="margin-bottom:5px;">{row['Nama']}</h4>
            <hr style="margin:5px 0;">
            <b>⭐ Rating:</b> {row['Rating']}<br>
            <b>💰 Harga:</b> {row['Harga']}<br>
            <b>🕒 Jam:</b> {row['Jam']}<br>
            <b>📍 Status:</b> <span style="color:{'green' if row['Status']=='Buka' else 'red'};">{row['Status']}</span>
        </div>
        """
        folium.Marker([row['lat'], row['lng']], 
                      popup=folium.Popup(html_popup, max_width=250), 
                      tooltip=row['Nama']).add_to(m)
    
    st_folium(m, width=1200, height=500)

except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan klik 'Jalankan Scraping Baru'.")