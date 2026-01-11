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
        # Pastikan GEMINI_API_KEY sudah diset di Streamlit Cloud Secrets
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        st.sidebar.warning("🤖 AI Gemini belum aktif (Cek API Key di Secrets).")
        return None

model_ai = inisialisasi_ai()

# 2. Sidebar Navigasi
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung atau Bakso")

if st.sidebar.button("Perbarui Data (Scraping)"):
    try:
        from scrapper import scrape_gmaps
        with st.spinner('Sedang melakukan scraping data asli (mohon tunggu)...'):
            # Menjalankan scrapper dan menyimpan ke data_jabar_umkm.csv
            scrape_gmaps("kuliner jawa barat", total_data=100)
            st.sidebar.success("Scraping Berhasil!")
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Gagal Scraping: {e}")

# 3. Main Logic (Blok Try Utama)
try:
    # Membaca data hasil scraping
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Logika Filter Dinamis
    if user_query:
        if search_type == "Kota/Kabupaten":
            filtered_df = df[df['Kota'].str.contains(user_query, case=False)]
            chart_col = 'Kategori'
            target_title = f"Analisis Peluang Usaha di {user_query}"
        else:
            filtered_df = df[df['Kategori'].str.contains(user_query, case=False)]
            chart_col = 'Kota'
            target_title = f"Analisis Lokasi Potensial untuk {user_query}"
    else:
        filtered_df = df
        chart_col = 'Kategori'
        target_title = "Gambaran Umum Kuliner Jawa Barat"

    st.title(f"🚀 {target_title}")

    # 4. Visualisasi Peluang Bisnis
    col1, col2 = st.columns(2)
    
    if not filtered_df.empty:
        with col1:
            fig_pie = px.pie(filtered_df, names=chart_col, title="Dominasi Pasar (Kompetitor)", hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        with col2:
            avg_rating = filtered_df.groupby(chart_col)['Rating'].mean().reset_index()
            fig_bar = px.bar(avg_rating, x=chart_col, y='Rating', color='Rating', 
                             title="Kualitas Layanan Kompetitor (Avg Rating)")
            st.plotly_chart(fig_bar, use_container_width=True)
            
        # 5. GIS (Geographic Information System)
        st.subheader("📍 Peta Sebaran & Jam Operasional Asli")
        # Titik tengah Jawa Barat secara default
        m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
        
        for i, row in filtered_df.head(50).iterrows():
            popup_html = f"""
            <div style='font-family: Arial; width: 200px;'>
                <b>{row['Nama']}</b><hr>
                🕒 <b>Jam:</b> {row['Jam']}<br>
                ⭐ <b>Rating:</b> {row['Rating']}<br>
                📍 <b>Status:</b> {row['Status']}
            </div>"""
            folium.Marker(
                [row['lat'], row['lng']], 
                popup=folium.Popup(popup_html, max_width=250),
                icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red", icon="info-sign")
            ).add_to(m)
        st_folium(m, width=1300, height=500)

        # 6. Fitur Konsultan AI Gemini
        st.markdown("---")
        st.subheader("🤖 Analisis Konsultan AI Gemini")
        
        if model_ai:
            user_msg = st.chat_input("Tanyakan strategi bisnis (misal: 'Bisnis bakso di Bandung bagusnya dimana?')")
            if user_msg:
                with st.chat_message("user"):
                    st.write(user_msg)
                with st.chat_message("assistant"):
                    try:
                        # Membuat ringkasan data sebagai konteks untuk AI
                        ringkasan_data = filtered_df[chart_col].value_counts().to_dict()
                        prompt = f"Berdasarkan data UMKM Jabar: {ringkasan_data}. Jawab pertanyaan strategi ini: {user_msg}"
                        
                        response = model_ai.generate_content(prompt)
                        st.markdown(response.text)
                    except Exception as ai_err:
                        st.error("AI sedang sibuk atau limit tercapai. Silakan coba beberapa saat lagi.")
        else:
            st.info("Chatbot AI akan muncul di sini setelah API Key dikonfigurasi.")
    else:
        st.warning(f"Tidak ada data ditemukan untuk '{user_query}'. Cobalah kata kunci lain atau perbarui data.")

# Penutup blok try utama (PENTING: Jangan sampai terhapus)
except FileNotFoundError:
    st.warning("⚠️ Data belum tersedia di server. Silakan klik tombol 'Perbarui Data (Scraping)' di sidebar sebelah kiri.")
except Exception as general_err:
    st.error(f"⚠️ Terjadi kesalahan aplikasi: {general_err}")
