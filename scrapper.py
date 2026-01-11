import time
import pandas as pd
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def scrape_jabar_raya(total_target=1500):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # DAFTAR 27 WILAYAH JAWA BARAT
    locations = {
        "Kota Bandung": (-6.9175, 107.6191), "Kab. Bandung": (-7.0251, 107.5197), 
        "Kab. Bandung Barat": (-6.8452, 107.4478), "Kota Bogor": (-6.5971, 106.8060), 
        "Kab. Bogor": (-6.4797, 106.8249), "Kota Depok": (-6.4025, 106.7942),
        "Kota Bekasi": (-6.2383, 106.9756), "Kab. Bekasi": (-6.2651, 107.1265), 
        "Kab. Karawang": (-6.3073, 107.2931), "Kab. Garut": (-7.2232, 107.9000),
        "Kab. Purwakarta": (-6.5567, 107.4428), "Kab. Subang": (-6.5715, 107.7587),
        "Kota Cirebon": (-6.7320, 108.5523), "Kab. Cirebon": (-6.7500, 108.4800),
        "Kab. Indramayu": (-6.3264, 108.3241), "Kab. Cianjur": (-6.8219, 107.1394),
        "Kab. Sukabumi": (-7.0000, 106.6000), "Kota Sukabumi": (-6.9277, 106.9300),
        "Kab. Sumedang": (-6.8589, 107.9164), "Kab. Majalengka": (-6.8361, 108.2274),
        "Kab. Kuningan": (-6.9764, 108.4828), "Kab. Ciamis": (-7.3262, 108.3533),
        "Kota Tasikmalaya": (-7.3274, 108.2207), "Kab. Tasikmalaya": (-7.4500, 108.1000),
        "Kab. Pangandaran": (-7.6833, 108.4833), "Kota Cimahi": (-6.8741, 107.5443),
        "Kota Banjar": (-7.3698, 108.5333)
    }
    
    categories = ["Bakso dan Mie Ayam", "Ayam Bakar", "Pecel Lele", "Sate","Nasi Padang", "Soto", "Nasi Goreng", "Bakmie", "Dimsum"]
    
    all_data = []
    
    # Setup Driver dengan penanganan error koneksi
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except:
        driver = webdriver.Chrome(options=chrome_options)

    print(f"=== Memulai Scraping Sistematis (Target Maksimal: {total_target} Data) ===")

    try:
        for loc_name, coords in locations.items():
            if len(all_data) >= total_target: break
            
            for cat in categories:
                if len(all_data) >= total_target: break
                
                query = f"{cat} di {loc_name}".replace(" ", "+")
                print(f"🔎 Mengambil data: {cat} di {loc_name}...")
                
                driver.get(f"http://www.google.com/maps/search/{query}")
                time.sleep(5) # Memberi waktu lebih untuk loading awal

                try:
                    # Scroll lebih dalam (5 kali) agar mendapatkan lebih banyak data per kategori
                    scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
                    for _ in range(5):
                        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                        time.sleep(1.5)
                except: pass

                # Ambil SEMUA data yang muncul (batasan [:10] dihapus)
                places = driver.find_elements(By.CLASS_NAME, "hfpxzc")
                
                for p in places:
                    if len(all_data) >= total_target: break # Berhenti jika sudah 1500
                    try:
                        name = p.get_attribute("aria-label")
                        parent_text = p.find_element(By.XPATH, "./../../..").text
                        
                        # Ekstraksi Rating
                        rating = 0.0
                        lines = parent_text.split('\n')
                        for line in lines:
                            if '(' in line and (',' in line or '.' in line):
                                try:
                                    rating = float(line.split('(')[0].strip().replace(',', '.'))
                                    break
                                except: continue

                        # Hindari duplikat nama
                        if name and name not in [d['Nama'] for d in all_data]:
                            all_data.append({
                                "Nama": name,
                                "Wilayah": loc_name,
                                "Kategori": cat,
                                "Rating": rating,
                                "Status": "Buka" if "Buka" in parent_text else "Tutup",
                                "lat": coords[0] + random.uniform(-0.02, 0.02),
                                "lng": coords[1] + random.uniform(-0.02, 0.02)
                            })
                    except: continue
            
            print(f"✅ Progres: {len(all_data)} data terkumpul.")

        # Simpan ke CSV
        df_final = pd.DataFrame(all_data)
        df_final.to_csv("data_jabar_umkm.csv", index=False)
        print(f"🎉 Scraping Selesai! Total data yang didapat: {len(df_final)}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Error Terjadi: {e}")
        if 'driver' in locals(): driver.quit()
        return False

if __name__ == "__main__":
    # Menjalankan dengan target 1500 data
    scrape_jabar_raya(1500)
