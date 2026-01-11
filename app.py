import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Strategic UMKM Advisor - Jabar", page_icon="🎯", layout="wide")

# --- FUNGSI HELPER: Grouping ---
def group_kategori(kat):
    kat = str(kat).lower()
    if 'bakso' in kat or 'mie ayam' in kat or 'bakmie' in kat: return 'Mie & Bakso'
    if 'ayam bakar' in kat or 'pecel lele' in kat or 'sate' in kat: return 'Lauk Bakar/Goreng'
    if 'padang' in kat or 'soto' in kat or 'nasi goreng' in kat: return 'Nasi & Soto'
    if 'dimsum' in kat: return 'Camilan & Dimsum'
    if 'kopi' in kat or 'cafe' in kat: return 'Kopi & Cafe'
    return 'Kuliner Lainnya'

# 2. Sidebar Navigation Utama
st.sidebar.markdown("### Analisis Peluang Usaha Kuliner UMKM")
menu = st.sidebar.radio(
    "Menu Utama:",
    ["💡 Kesimpulan Strategis", "🔍 Market Finder", "📊 Analisis Visual", "📍 Peta GIS Jabar"]
)

st.sidebar.markdown("---")

# 3. Logika Loading Data & Filter Global
if os.path.exists("data_jabar_umkm.csv"):
    df = pd.read_csv("data_jabar_umkm.csv")
    df['Rating'] = pd.to_numeric(df['Rating'], errors='coerce').fillna(0.0)
    df['Kelompok_Bisnis'] = df['Kategori'].apply(group_kategori)
    col_wil = 'Wilayah' if 'Wilayah' in df.columns else 'Kota'

    # --- FILTER GLOBAL (Agar tidak reset saat pindah menu) ---
    st.sidebar.markdown("### 📍 Filter Global")
    list_wilayah = ["Seluruh Jawa Barat"] + sorted(df[col_wil].unique().tolist())
    
    selected_city = st.sidebar.selectbox(
        "Pilih Lokasi Analisis:", 
        list_wilayah, 
        key="global_city_selector"
    )
    
    # Filter Data Global
    f_df = df if selected_city == "Seluruh Jawa Barat" else df[df[col_wil] == selected_city]
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("🚀 Scrape Data Real-Time", use_container_width=True):
        from scrapper import scrape_jabar_raya
        with st.spinner('Menghubungkan ke Google Maps...'):
            if scrape_jabar_raya(1100):
                st.rerun()

    # --- ISI KONTEN BERDASARKAN MENU ---

    if menu == "💡 Kesimpulan Strategis":
        st.markdown(f"# 💡 Konsultasi Strategi Bisnis: {selected_city}")
        st.caption("Analisis kecerdasan bisnis (Business Intelligence) untuk menentukan arah investasi UMKM.")
        
        if not f_df.empty:
            counts = f_df['Kategori'].value_counts()
            ratings = f_df.groupby('Kategori')['Rating'].mean()
            
            # Tampilan Metrik Utama
            c1, c2, c3 = st.columns(3)
            with c1:
                st.success(f"### ✅ Peluang Emas\n**{counts.idxmin()}**")
                st.write(f"Kompetitor: {counts.min()} Unit")
            with c2:
                st.warning(f"### ⚠️ Pasar Jenuh\n**{counts.idxmax()}**")
                st.write(f"Kompetitor: {counts.max()} Unit")
            with c3:
                st.error(f"### 🚩 Kualitas Pasar\n**{ratings.idxmax()}**")
                st.write(f"Avg Rating: {ratings.max():.1f} ⭐")
            
            st.markdown("---")
            
            # --- NARASI ANALISIS MENDALAM ---
            st.subheader("📌 Laporan Rekomendasi Manajerial")
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.info(f"""
                **1. Strategi Penetrasi (Blue Ocean):** Di wilayah {selected_city}, kategori **{counts.idxmin()}** menunjukkan tingkat persaingan terendah dengan hanya {counts.min()} unit usaha terdeteksi. 
                Ini adalah peluang "Blue Ocean" di mana Anda dapat memposisikan diri sebagai pemimpin pasar lebih cepat. 
                Kurangnya pilihan bagi konsumen di sektor ini memungkinkan Anda memiliki kontrol harga yang lebih baik.
                """)
                
                st.info(f"""
                **2. Analisis Risiko (Red Ocean):** Kategori **{counts.idxmax()}** telah mencapai titik jenuh di {selected_city} dengan {counts.max()} kompetitor. 
                Memasuki pasar ini tanpa inovasi radikal sangat berisiko tinggi karena akan terjebak dalam perang harga. 
                Anda membutuhkan *Unique Selling Point* (USP) yang sangat kuat jika ingin berkompetisi di sini.
                """)

            with col_b:
                st.info(f"""
                **3. Standar Ekspektasi Konsumen:** Berdasarkan data rating, kategori **{ratings.idxmax()}** memiliki standar kualitas tertinggi ({ratings.max():.1f} ⭐). 
                Hal ini menunjukkan bahwa konsumen di wilayah ini sangat selektif dan melek kualitas. 
                Pastikan operasional bisnis Anda memiliki standar kontrol kualitas yang ketat untuk memenuhi ekspektasi pasar yang tinggi ini.
                """)
                
                st.info(f"""
                **4. Rencana Aksi (Action Plan):** Kami menyarankan Anda untuk segera mengevaluasi titik koordinat spesifik melalui menu **Peta GIS**. 
                Carilah pemukiman padat atau pusat keramaian di {selected_city} yang belum memiliki unit usaha **{counts.idxmin()}**. 
                Inovasi pada kemasan dan digital marketing akan mempercepat akuisisi pelanggan di wilayah potensial ini.
                """)
        else:
            st.warning("Data belum tersedia untuk wilayah ini.")

    elif menu == "🔍 Market Finder":
        st.markdown("# 🔍 Market Opportunity Finder")
        st.write("Gunakan alat ini untuk mencari Kota/Kabupaten mana yang paling potensial bagi jenis usaha pilihan Anda.")
        
        sel_cat = st.selectbox("Pilih Kategori Usaha yang Ingin Anda Buka:", sorted(df['Kategori'].unique().tolist()))
        
        if sel_cat:
            cat_df = df[df['Kategori'] == sel_cat]
            opp_df = cat_df.groupby(col_wil).agg({
                'Nama': 'count',
                'Rating': 'mean'
            }).reset_index().sort_values(by='Nama', ascending=True)
            
            opp_df.columns = ['Wilayah', 'Jumlah Saingan', 'Kualitas Layanan (Rating)']
            
            st.success(f"### 🏆 3 Lokasi Terbaik untuk Membuka Usaha **{sel_cat}**")
            top_3 = opp_df.head(3)
            cols = st.columns(3)
            for i, (idx, row) in enumerate(top_3.iterrows()):
                with cols[i]:
                    st.metric(f"Peringkat {i+1}", row['Wilayah'], f"{int(row['Jumlah Saingan'])} Kompetitor")
            
            st.markdown("---")
            st.subheader("📋 Perbandingan Kompetisi Seluruh Wilayah")
            st.dataframe(opp_df, use_container_width=True)

    elif menu == "📊 Analisis Visual":
        st.markdown(f"# 📊 Perbandingan Industri: {selected_city}")
        if not f_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(px.pie(f_df, names='Kelompok_Bisnis', title="Dominasi Sektor Kuliner", hole=0.4), use_container_width=True)
            with col2:
                avg_df = f_df.groupby('Kelompok_Bisnis')['Rating'].mean().reset_index()
                st.plotly_chart(px.bar(avg_df, x='Kelompok_Bisnis', y='Rating', color='Rating', title="Tingkat Kepuasan Pelanggan", range_y=[0,5], text_auto='.1f'), use_container_width=True)

    elif menu == "📍 Peta GIS Jabar":
        st.markdown(f"# 📍 Sebaran Lokasi Kompetitor: {selected_city}")
        if not f_df.empty:
            m = folium.Map(location=[f_df['lat'].mean(), f_df['lng'].mean()], zoom_start=11)
            marker_cluster = MarkerCluster().add_to(m)
            for _, row in f_df.iterrows():
                warna = "blue" if row['Status'] == "Buka" else "red"
                folium.Marker(
                    [row['lat'], row['lng']], 
                    popup=f"<b>{row['Nama']}</b><br>Kategori: {row['Kategori']}<br>Status: {row['Status']}",
                    icon=folium.Icon(color=warna, icon="cutlery", prefix="fa")
                ).add_to(marker_cluster)
            st_folium(m, width=1300, height=600)

else:
    st.title("📊 Strategic Advisor UMKM Jawa Barat")
    st.info("Database belum ditemukan. Silakan klik tombol 'Scrape Data Real-Time' di sidebar untuk mengumpulkan data.")

st.sidebar.markdown("---")
st.sidebar.caption("© Hak Cipta Kelompok Superman")
