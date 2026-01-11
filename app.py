import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
from datetime import datetime, timedelta

# 1. Konfigurasi Halaman & AI Gemini
st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

def inisialisasi_ai():
    try:
        # Mengambil API Key dari Secrets Streamlit Cloud
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.sidebar.error("AI Gemini belum terkonfigurasi (Cek Secrets).")
        return None

model_ai = inisialisasi_ai()

# 2. Sidebar Filter Analisis
st.sidebar.title("🔍 Filter Analisis UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan Nama {search_type}:", placeholder="Contoh: Bandung atau Bakso")

if st.sidebar.button("Perbarui Data (Scraping)"):
    try:
        from scrapper import scrape_gmaps
        with st.spinner('Mengambil data terbaru dari Google Maps...'):
            scrape_gmaps("kuliner jawa barat", total_data=1000)
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Gagal Scraping: {e}")

# 3. Pengolahan Data Peluang Usaha
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Logika Filter Dinamis
    if user_query:
        if search_type == "Kota/Kabupaten":
            filtered_df = df[df['Kota'].str.contains(user_query, case=False)]
            logic_title = f"Analisis Peluang Kategori Makanan di {user_query}"
            chart_col = 'Kategori'
        else:
            filtered_df = df[df['Kategori'].str.contains(user_query, case=False)]
            logic_title = f"Analisis Peluang Lokasi untuk Bisnis {user_query}"
            chart_col = 'Kota'
    else:
        filtered_df = df
        logic_title = "Gambaran Umum Kuliner Jawa Barat"
        chart_col = 'Kategori'

    # --- TAMPILAN UTAMA ---
    st.title("🚀 Platform Analisis Peluang Usaha UMKM Kuliner")
    st.subheader(logic_title)

    # 4. Visualisasi Data (Pie Chart & Bar Chart)
    col1, col2 = st.columns(2)
    with col1:
        fig_pie = px.pie(filtered_df, names=chart_col, title="Dominasi Pasar Saat Ini", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col2:
        # Menghitung rata-rata rating kompetitor per grup
        avg_rating = filtered_df.groupby(chart_col)['Rating'].mean().reset_index()
        fig_bar = px.bar(avg_rating, x=chart_col, y='Rating', color='Rating', title="Kualitas Kompetitor (Avg Rating)")
        st.plotly_chart(fig_bar, use_container_width=True)

    # 5. Fitur GIS (Geographic Information System)
    st.subheader("📍 Peta Sebaran Kompetitor")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for i, row in filtered_df.head(50).iterrows():
        popup_info = f"<b>{row['Nama']}</b><br>Rating: {row['Rating']}<br>Harga: {row['Harga']}"
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(popup_info, max_width=200)).add_to(m)
    st_folium(m, width=1300, height=500)

    # 6. Fitur Konsultan AI Gemini
    st.markdown("---")
    st.subheader("🤖 Konsultan Strategi Bisnis AI")
    
    if model_ai:
        user_ask = st.chat_input("Tanyakan strategi pemasaran atau analisis kompetitor...")
        if user_ask:
            # Mengirim konteks data ke AI untuk analisis cerdas
            context = f"""
            Data UMKM saat ini: Lokasi {user_query if user_query else 'Jabar'}, 
            Kategori dominan: {filtered_df[chart_col].mode()[0] if not filtered_df.empty else 'N/A'}.
            User bertanya: {user_ask}
            Berikan saran taktis untuk pengusaha UMKM.
            """
            with st.chat_message("assistant"):
                response = model_ai.generate_content(context)
                st.markdown(response.text)

except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan jalankan 'Perbarui Data' di sidebar.")
