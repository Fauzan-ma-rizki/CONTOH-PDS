import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. Konfigurasi Halaman & AI Gemini
st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

# Masukkan API Key Gemini Anda di sini atau lewat Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-pro')
except:
    st.error("API Key Gemini tidak ditemukan. Fitur Chat AI dinonaktifkan.")

# 2. Sidebar & Kontrol Data
st.sidebar.title("🔍 Filter Analisis UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan Nama {search_type}:", placeholder="Contoh: Bandung atau Bakso")

# Tombol Scraping (Tetap ada untuk update data)
if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner('Mengambil data terbaru dari Google Maps...'):
        scrape_gmaps("kuliner jawa barat", total_data=1000)
        st.rerun()

# 3. Pengolahan Data
try:
    df = pd.read_csv("data_bandung.csv") # Pastikan scrapper sudah jalan
    
    # Logika Filter Dinamis
    if user_query:
        if search_type == "Kota/Kabupaten":
            # (Simulasi filter kota karena data scrap biasanya spesifik area)
            filtered_df = df.copy() 
            logic_title = f"Analisis Peluang Kategori Makanan di {user_query}"
            chart_names = 'Kategori' # Jika cari kota, tampilkan peluang kategori
        else:
            filtered_df = df[df['Kategori'].str.contains(user_query, case=False)]
            logic_title = f"Analisis Peluang Lokasi untuk Bisnis {user_query}"
            chart_names = 'Nama' # (Atau kolom Kota jika tersedia)
    else:
        filtered_df = df
        logic_title = "Gambaran Umum Kuliner Jawa Barat"
        chart_names = 'Kategori'

    # --- TAMPILAN UTAMA ---
    st.title("🚀 Platform Analisis Peluang Usaha UMKM Kuliner")
    st.subheader(logic_title)

    # 4. Visualisasi Peluang Usaha
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie Chart Peluang Usaha
        fig_pie = px.pie(filtered_df, names=chart_names, title="Persentase Dominasi Pasar", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        st.caption("Irisan terkecil menunjukkan 'Blue Ocean' (Persaingan Rendah/Peluang Tinggi).")

    with col2:
        # Grafik Rating per Kategori
        fig_bar = px.bar(filtered_df.groupby(chart_names)['Rating'].mean().reset_index(), 
                         x=chart_names, y='Rating', color='Rating', 
                         title="Kualitas Kompetitor (Rata-rata Rating)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # 5. Fitur GIS (Peta Sebaran)
    st.subheader("📍 Peta Sebaran Kompetitor & Lokasi Strategis")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for i, row in filtered_df.head(50).iterrows():
        popup_html = f"<b>{row['Nama']}</b><br>Rating: {row['Rating']}<br>Harga: {row['Harga']}"
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(popup_html, max_width=200)).add_to(m)
    st_folium(m, width=1300, height=500)

    # 6. Analisis Kesimpulan Terbaik (Decision Support)
    st.markdown("---")
    st.subheader("📋 Kesimpulan Strategis")
    
    # Logika sederhana: Cari kategori dengan jumlah sedikit tapi rating tinggi
    rekomendasi = filtered_df['Kategori'].value_counts().idxmin()
    st.success(f"**Rekomendasi Utama:** Berdasarkan data, peluang usaha **{rekomendasi}** sangat tinggi di area ini karena persaingan masih minim.")

    # 7. AI Konsultan Bisnis (Gemini)
    st.markdown("---")
    st.subheader("🤖 Konsultan Bisnis AI (Gemini)")
    user_ask = st.chat_input("Tanyakan strategi pemasaran atau modal usaha...")
    
    if user_ask:
        with st.chat_message("user"):
            st.write(user_ask)
        
        prompt = f"""Anda adalah pakar UMKM Jabar. User bertanya: '{user_ask}'. 
        Berikan jawaban berdasarkan data: Kategori terbanyak adalah {filtered_df['Kategori'].iloc[0]} 
        dengan rata-rata rating {filtered_df['Rating'].mean():.1f}."""
        
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                response = model.generate_content(prompt)
                st.write(response.text)

except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan jalankan Scraping di sidebar.")
