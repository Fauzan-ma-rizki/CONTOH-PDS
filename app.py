import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

# Konfigurasi Halaman
st.set_page_config(page_title="Big Data UMKM Jawa Barat", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { 
        background-color: #ffffff; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
        border-left: 5px solid #007bff;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR MENU ---
st.sidebar.title("📊 Business Dashboard")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3168/3168190.png", width=100)

# Menu Navigasi
menu = st.sidebar.radio(
    "Pilih Menu Visualisasi:",
    ["💡 Kesimpulan Strategis", "📈 Analisis Grafik", "📍 Pemetaan GIS (Peta)"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Wilayah")

# --- LOGIKA DATA ---
try:
    df = pd.read_csv("data_jabar_umkm.csv")
    # Pastikan Rating adalah tipe numerik
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    
    # Filter Wilayah (Nama Kota)
    list_kota = ["Seluruh Jawa Barat"] + sorted(df['Kota'].unique().tolist())
    selected_city = st.sidebar.selectbox("Pilih Kota/Kabupaten:", list_kota)

    # Tombol Scraping diletakkan di bawah filter
    st.sidebar.markdown("---")
    if st.sidebar.button("🚀 Perbarui 1000 Data Jabar"):
        from scrapper import scrape_jabar_raya
        with st.spinner('Proses scraping sedang berjalan...'):
            if scrape_jabar_raya(1000):
                st.success("✅ Data Berhasil Diperbarui!")
                st.rerun()

    # Eksekusi Filter Wilayah
    filtered_df = df.copy()
    if selected_city != "Seluruh Jawa Barat":
        filtered_df = filtered_df[filtered_df['Kota'] == selected_city]

    # --- ROUTING HALAMAN BERDASARKAN MENU ---

    if menu == "💡 Kesimpulan Strategis":
        st.title(f"💡 Analisis Peluang Bisnis: {selected_city}")
        if not filtered_df.empty:
            counts = filtered_df['Kategori'].value_counts()
            avg_ratings = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
            
            st.markdown("### Ringkasan Eksekutif")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.success(f"### ✅ Peluang Emas\n**{counts.idxmin()}**")
                st.caption(f"Kategori dengan persaingan terendah ({counts.min()} kompetitor).")
            with c2:
                st.warning(f"### ⚠️ Peluang Sulit\n**{counts.idxmax()}**")
                st.caption(f"Pasar paling jenuh ({counts.max()} kompetitor).")
            with c3:
                # Cari rating tertinggi
                best_cat = avg_ratings.loc[avg_ratings['Rating'].idxmax()]
                st.error(f"### 🚩 Risiko Kualitas\n**{best_cat['Kategori']}**")
                st.caption(f"Ekspektasi pelanggan sangat tinggi (Avg Rating {best_cat['Rating']:.1f}).")
            
            st.markdown("---")
            st.info(f"👉 **Strategi Rekomendasi:** Untuk wilayah **{selected_city}**, sektor **{counts.idxmin()}** menawarkan hambatan masuk (barrier to entry) terendah. Disarankan untuk memfokuskan investasi pada sektor ini.")
        else:
            st.warning("Data tidak tersedia. Silakan perbarui data di sidebar.")

    elif menu == "📈 Analisis Grafik":
        st.title(f"📈 Distribusi Pasar & Kualitas: {selected_city}")
        if not filtered_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                fig_pie = px.pie(filtered_df, names='Kategori', title="Market Share Kompetitor", hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                avg_df = filtered_df.groupby('Kategori')['Rating'].mean().reset_index()
                fig_bar = px.bar(avg_df, x='Kategori', y='Rating', color='Rating', 
                                 title="Kualitas Layanan (Avg Rating)", 
                                 color_continuous_scale='RdYlGn', range_y=[0,5],
                                 text_auto='.1f')
                st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("Data tidak tersedia.")

    elif menu == "📍 Pemetaan GIS (Peta)":
        st.title(f"📍 Pemetaan Lokasi Kompetitor: {selected_city}")
        if not filtered_df.empty:
            map_center = [filtered_df['lat'].mean(), filtered_df['lng'].mean()]
            m = folium.Map(location=map_center, zoom_start=12 if selected_city != "Seluruh Jawa Barat" else 9)
            
            marker_cluster = MarkerCluster().add_to(m)

            for _, row in filtered_df.iterrows():
                color = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    location=[row['lat'], row['lng']],
                    popup=f"<b>{row['Nama']}</b><br>⭐ {row['Rating']}<br>🕒 {row['Jam']}",
                    icon=folium.Icon(color=color, icon="utensils", prefix="fa")
                ).add_to(marker_cluster)
            
            st_folium(m, width=1300, height=600)
        else:
            st.warning("Data tidak tersedia.")

except Exception as e:
    st.info("👋 Selamat Datang! Silakan klik tombol 'Perbarui 1000 Data Jabar' di sidebar untuk menginisialisasi database.")

st.sidebar.markdown("---")
st.sidebar.caption("Sistem Informasi Geografis UMKM Jabar © 2026")
