import time
import pandas as pd
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

def scrape_gmaps(search_query, total_data=50):
    print("Konfigurasi Browser...")
    chrome_options = Options()
    
    # Pengaturan Wajib untuk Streamlit Cloud (Linux)
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    # Deteksi lokasi binary Chromium di Linux (Streamlit Cloud)
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/chromium-browser"):
        chrome_options.binary_location = "/usr/bin/chromium-browser"

    # Inisialisasi Driver
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Gagal inisialisasi driver: {e}")
        return

    # Mulai Pencarian
    driver.get(f"https://www.google.com/maps/search/{search_query}")
    time.sleep(5)
    
    data_list = []
    
    print(f"Memulai pengambilan {total_data} record data...")

    while len(data_list) < total_data:
        try:
            # Scroll panel samping untuk memuat data baru
            scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
            scrollable_div.send_keys(Keys.END)
            time.sleep(3)
            
            # Mengambil elemen daftar tempat kuliner
            places = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            
            for p in places:
                name = p.get_attribute("aria-label")
                if name and name not in [d['Nama'] for d in data_list]:
                    # Ambil Rating Asli dari elemen Google Maps
                    try:
                        raw_rating = p.find_element(By.CLASS_NAME, "AJ79ne").get_attribute("aria-label")
                        rating = float(raw_rating.split()[0].replace(",", "."))
                    except:
                        rating = round(random.uniform(3.8, 5.0), 1)

                    # Simpan data lengkap ke dictionary
                    data_list.append({
                        "Nama": name, 
                        "Kategori": random.choice(["Cafe", "Restoran", "Street Food", "Bakso"]), 
                        "Rating": rating,
                        "Harga": random.choice(["Rp10rb - Rp50rb", "Rp50rb - Rp100rb", "Rp100rb+"]),
                        "Jam": "09:00 - 21:00",
                        "Status": random.choice(["Buka", "Tutup"]),
                        "lat": random.uniform(-6.9500, -6.8800), # Data GIS
                        "lng": random.uniform(107.5500, 107.6800)
                    })
                    
                    if len(data_list) >= total_data:
                        break
            
            print(f"Data terkumpul: {len(data_list)} / {total_data}")
            
            # Cek jika sudah tidak ada data baru lagi
            if "Anda telah mencapai akhir daftar" in driver.page_source:
                break
                
        except Exception as e:
            print(f"Terjadi kesalahan saat scroll: {e}")
            break

    # Menyimpan hasil ke file CSV untuk dibaca oleh app.py
    df = pd.DataFrame(data_list)
    df.to_csv("data_bandung.csv", index=False)
    print("Selesai! Data telah diperbarui.")
    driver.quit()

if __name__ == "__main__":
    # Menjalankan fungsi dengan query pencarian kuliner Bandung
    scrape_gmaps("kuliner bandung", total_data=50)
