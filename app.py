import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 1. Konfigurasi AI & Safety
@st.cache_resource
def load_gemini_model():
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        return genai.GenerativeModel(
            'gemini-1.5-flash',
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
    except: return None

model_ai = load_gemini_model()
st.set_page_config(page_title="Analisis UMKM Jabar", layout="wide")

# 2. Sidebar
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung atau Bakso")

if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner('Scraping data asli sedang berjalan...'):
        scrape_gmaps("kuliner jawa barat", total_data=50) # Set 50 agar lebih cepat
        st.rerun()

# 3. Main Logic
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    if user_query:
        mask = df['Kota'].str.contains(user_query, case=False) if search_type == "Kota/Kabupaten" else df['Kategori'].str.contains(user_query, case=False)
        filtered_df = df[mask]
        chart_col = 'Kategori' if search_type == "Kota/Kabupaten" else 'Kota'
        target = f"Peluang di {user_query}"
    else:
        filtered_df = df
        chart_col = 'Kategori'
        target = "Seluruh Jawa Barat"

    st.title(f"🚀 {target}")

    # Visualisasi
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(filtered_df, names=chart_col, title="Dominasi Pasar", hole=0.4), use_container_width=True)
    with c2:
        if not filtered_df.empty:
            avg_rating = filtered_df.groupby(chart_col)['Rating'].mean().reset_index()
            st.plotly_chart(px.bar(avg_rating, x=chart_col, y='Rating', color='Rating', title="Rata-rata Rating"), use_container_width=True)

    # GIS
    st.subheader("📍 Peta Sebaran & Jam Operasional")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for _, row in filtered_df.head(50).iterrows():
        html = f"<b>{row['Nama']}</b><br>🕒 {row['Jam']}<br>⭐ {row['Rating']}"
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(html, max_width=200),
                      icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red")).add_to(m)
    st_folium(m, width=1300, height=450)

    # Gemini AI
    st.markdown("---")
    st.subheader("🤖 Analisis Konsultan AI Gemini")
    if model_ai:
        user_msg = st.chat_input("Tanyakan strategi bisnis...")
        if user_msg:
            with st.chat_message("user"): st.write(user_msg)
            with st.chat_message("assistant"):
                try:
                    stats = filtered_df[chart_col].value_counts().head(5).to_dict()
                    prompt = f"Data UMKM: {stats}. Pertanyaan: {user_msg}. Berikan saran singkat."
                    response = model_ai.generate_content(prompt)
                    st.write(response.text)
                except: st.error("AI Limit Tercapai. Mohon tunggu 1 menit sebelum bertanya lagi.")
    else: st.warning("AI tidak aktif. Periksa API Key di Secrets.")

except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan klik 'Perbarui Data' di sidebar.")
