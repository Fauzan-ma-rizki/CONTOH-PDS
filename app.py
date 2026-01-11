import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from google import genai # Pustaka Baru
import os

# 1. Konfigurasi Client AI Baru (SDK v1)
@st.cache_resource
def load_genai_client():
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        return client
    except Exception as e:
        return None

client_ai = load_genai_client()

st.set_page_config(page_title="Analisis Peluang UMKM Jabar", layout="wide")

# 2. Sidebar
st.sidebar.title("🔍 Navigasi UMKM")
search_type = st.sidebar.radio("Cari Berdasarkan:", ["Kota/Kabupaten", "Kategori Makanan"])
user_query = st.sidebar.text_input(f"Masukkan {search_type}:", placeholder="Contoh: Bandung")

if st.sidebar.button("Perbarui Data (Scraping)"):
    try:
        from scrapper import scrape_gmaps
        with st.spinner('Scraping data asli sedang berjalan...'):
            scrape_gmaps("kuliner jawa barat", total_data=50)
            st.rerun()
    except Exception as e:
        st.sidebar.error(f"Gagal Scraping: {e}")

# 3. Main Logic
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    
    if user_query:
        mask = df['Kota'].str.contains(user_query, case=False) if search_type == "Kota/Kabupaten" else df['Kategori'].str.contains(user_query, case=False)
        filtered_df = df[mask]
        chart_col = 'Kategori' if search_type == "Kota/Kabupaten" else 'Kota'
        target_name = f"di {user_query}"
    else:
        filtered_df = df
        chart_col = 'Kategori'
        target_name = "Jawa Barat"

    st.title(f"🚀 Analisis Peluang Bisnis {target_name}")

    # Visualisasi
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.pie(filtered_df, names=chart_col, title="Dominasi Kompetitor", hole=0.4), use_container_width=True)
    with c2:
        if not filtered_df.empty:
            avg_rating = filtered_df.groupby(chart_col)['Rating'].mean().reset_index()
            st.plotly_chart(px.bar(avg_rating, x=chart_col, y='Rating', color='Rating', title="Rata-rata Rating Kompetitor"), use_container_width=True)

    # GIS (Geographic Information System)
    st.subheader("📍 Peta Sebaran & Jam Operasional Asli")
    m = folium.Map(location=[-6.9175, 107.6191], zoom_start=12)
    for _, row in filtered_df.head(50).iterrows():
        popup_info = f"<b>{row['Nama']}</b><br>🕒 {row['Jam']}<br>⭐ {row['Rating']}"
        folium.Marker([row['lat'], row['lng']], popup=folium.Popup(popup_info, max_width=200),
                      icon=folium.Icon(color="blue" if row['Status']=="Buka" else "red")).add_to(m)
    st_folium(m, width=1300, height=450)

    # Chat AI Gemini (SDK v1)
    st.markdown("---")
    st.subheader("🤖 Konsultan Strategi Bisnis (Gemini v1)")
    if client_ai:
        user_msg = st.chat_input("Tanyakan strategi pemasaran atau modal usaha...")
        if user_msg:
            with st.chat_message("user"): st.write(user_msg)
            with st.chat_message("assistant"):
                try:
                    stats = filtered_df[chart_col].value_counts().head(5).to_dict()
                    prompt = f"Data UMKM: {stats}. Pertanyaan: {user_msg}. Berikan saran bisnis singkat."
                    
                    # Pemanggilan model menggunakan SDK baru
                    response = client_ai.models.generate_content(
                        model='gemini-1.5-flash',
                        contents=prompt
                    )
                    st.write(response.text)
                except Exception as e:
                    st.error("AI sedang sibuk atau limit tercapai. Tunggu 1 menit.")
    else:
        st.warning("Konfigurasi AI belum lengkap. Periksa API Key di Secrets.")

except FileNotFoundError:
    st.warning("Data belum tersedia. Silakan klik 'Perbarui Data' di sidebar.")
except Exception as e:
    st.error(f"Error Sistem: {e}")
