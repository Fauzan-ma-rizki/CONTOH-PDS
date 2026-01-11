import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
from datetime import datetime, timedelta

# Konfigurasi Gemini
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model_ai = genai.GenerativeModel('gemini-1.5-flash')
except:
    model_ai = None

st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

# Sidebar
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung atau Bakso")

if st.sidebar.button("Perbarui Data (Scraping)"):
    from scrapper import scrape_gmaps
    with st.spinner('Scraping data asli...'):
        scrape_gmaps("kuliner jawa barat", total_data=100)
        st.rerun()

# Main Logic
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    # Filter Data
    if user_query:
        if search_type == "Kota/Kabupaten":
            filtered_df = df[df['Kota'].str.contains(user_query, case=False)]
            chart_col = 'Kategori'
            target = f"Peluang Usaha di {user_query}"
        else:
            filtered_df = df[df['Kategori'].str.contains(user_query, case=False)]
            chart_col = 'Kota'
            target = f"Peluang Lokasi untuk {user_query}"
    else:
        filtered_df = df
        chart_col = 'Kategori'
        target = "Seluruh Jawa Barat"

    st.title(f"🚀 {target}")

    # Visualisasi
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(filtered_df, names=chart_col, title="Dominasi Kompetitor", hole=0.4))
    with c2:
        fig_bar = px.bar(filtered_df.groupby(chart_col)['Rating'].mean().reset_index(), 
                         x=chart_col, y='Rating', color='Rating', title="Kualitas Layanan Kompetitor")
        st.plotly_chart(fig_bar)

    # GIS
    st.subheader("📍 Peta Lokasi & Jam Operasional Asli")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for i, row in filtered_df.head(50).iterrows():
        popup_html = f"""
        <div style='font-family: Arial; width: 200px;'>
            <b>{row['Nama']}</b><hr>
            🕒 <b>Jam:</b> {row['Jam']}<br>
            ⭐ <b>Rating:</b> {row['Rating']}<br>
            📍 <b>Status:</b> {row['Status']}
        </div>"""
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(popup_html, max_width=250),
                      icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red")).add_to(m)
    st_folium(m, width=1300, height=500)

    # Gemini AI
    st.markdown("---")
    st.subheader("🤖 Analisis Konsultan AI Gemini")
    
    if model_ai is not None:
        user_msg = st.chat_input("Tanyakan strategi bisnis...")
        
        if user_msg:
            # Tampilkan pesan user di chat
            with st.chat_message("user"):
                st.markdown(user_msg)
            
            # Respon Assistant
            with st.chat_message("assistant"):
                with st.spinner("Sedang memikirkan strategi..."):
                    try:
                        # Menyiapkan konteks data agar AI tidak bingung jika data kosong
                        if not filtered_df.empty:
                            ringkasan = filtered_df[chart_col].value_counts().to_dict()
                            konteks = f"Data UMKM saat ini: {ringkasan}."
                        else:
                            konteks = "Data UMKM saat ini kosong."
                        
                        # Gabungkan konteks dengan pertanyaan user
                        full_prompt = f"{konteks} Pertanyaan user: {user_msg}. Berikan saran bisnis yang taktis."
                        
                        # Memanggil API
                        response = model_ai.generate_content(full_prompt)
                        
                        if response.text:
                            st.markdown(response.text)
                        else:
                            st.warning("AI memberikan respon kosong.")
                            
                    except Exception as e:
                        # Menangani error API (NotFound, Quota, dll) dengan elegan
                        st.error(f"Gagal mendapatkan respon AI. Error: {e}")
    else:
        st.warning("Fitur AI tidak aktif karena API Key tidak valid.")


