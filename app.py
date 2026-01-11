import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Konfigurasi AI & Keamanan
@st.cache_resource
def inisialisasi_ai():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
        # Menggunakan 1.5-flash karena lebih cepat dan kuota lebih banyak
        return genai.GenerativeModel(
            'gemini-1.5-flash',
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    except:
        return None

model_ai = inisialisasi_ai()

st.set_page_config(page_title="UMKM Jabar Business Analyst", layout="wide")

# 2. Sidebar Filter
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung")

if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner('Scraping data asli sedang berjalan...'):
        scrape_gmaps("kuliner jawa barat", total_data=100)
        st.rerun()

# 3. Logika Utama
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    if user_query:
        # Filter data berdasarkan input user
        if search_type == "Kota/Kabupaten":
            filtered_df = df[df['Kota'].str.contains(user_query, case=False)]
            chart_col = 'Kategori'
        else:
            filtered_df = df[df['Kategori'].str.contains(user_query, case=False)]
            chart_col = 'Kota'
    else:
        filtered_df = df
        chart_col = 'Kategori'

    st.title(f"🚀 Analisis Peluang Bisnis: {user_query if user_query else 'Jawa Barat'}")

    # Visualisasi Peluang
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(filtered_df, names=chart_col, title="Dominasi Kompetitor", hole=0.4), use_container_width=True)
    with col2:
        if not filtered_df.empty:
            avg_rating = filtered_df.groupby(chart_col)['Rating'].mean().reset_index()
            st.plotly_chart(px.bar(avg_rating, x=chart_col, y='Rating', color='Rating', title="Rata-rata Rating"), use_container_width=True)

    # GIS Map
    st.subheader("📍 Peta Sebaran Kompetitor & Jam Operasional")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for _, row in filtered_df.head(50).iterrows():
        popup = f"<b>{row['Nama']}</b><br>🕒 {row['Jam']}<br>⭐ {row['Rating']}"
        folium.Marker([row['lat'], row['lng']], 
                      popup=folium.Popup(popup, max_width=200),
                      icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red")).add_to(m)
    st_folium(m, width=1300, height=450)

    # Chat AI Gemini
    st.markdown("---")
    st.subheader("🤖 Konsultan AI Gemini")
    if model_ai:
        user_msg = st.chat_input("Tanyakan strategi bisnis...")
        if user_msg:
            with st.chat_message("user"): st.write(user_msg)
            with st.chat_message("assistant"):
                try:
                    # Kirim ringkasan data agar tidak kena limit token
                    ringkasan = filtered_df[chart_col].value_counts().head(5).to_dict()
                    prompt = f"Data UMKM Jabar: {ringkasan}. Berikan saran bisnis singkat untuk pertanyaan: {user_msg}"
                    response = model_ai.generate_content(prompt)
                    st.write(response.text)
                except:
                    st.error("AI Limit Tercapai. Mohon tunggu 1 menit.")
    else:
        st.warning("AI tidak aktif. Periksa API Key di Secrets.")

# Penutup blok try
except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan klik 'Perbarui Data' di sidebar.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {e}")
