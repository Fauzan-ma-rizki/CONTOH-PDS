import time
import pandas as pd
import random
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

def scrape_jabar_raya(total_target=10):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Tambahkan User-Agent agar tidak dianggap bot oleh Google
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    cities = {
        "Bandung": (-6.9175, 107.6191), "Bekasi": (-6.2383, 106.9756),
        "Bogor": (-6.5971, 106.8060), "Depok": (-6.4025, 106.7942),
        "Cirebon": (-6.7320, 108.5523), "Sukabumi": (-6.9277, 106.9300),
        "Tasikmalaya": (-7.3274, 108.2207), "Karawang": (-6.3073, 107.2931),
        "Cimahi": (-6.8741, 107.5443), "Garut": (-7.2232, 107.9000)
    }
    
    data_per_city = total_target // len(cities)
    all_data = []

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        for city, coords in cities.items():
            if len(all_data) >= total_target: break
            
            print(f"Scraping di {city}...")
            # Menggunakan URL pencarian langsung agar lebih akurat
            driver.get(f"https://www.google.com/maps/search/kuliner+di+{city}")
            time.sleep(8) # Tunggu lebih lama agar rating muncul

            try:
                scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
                for _ in range(15): 
                    driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
                    time.sleep(2)
            except: pass

            # Mengambil elemen kontainer utama tiap toko
            places = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            
            count = 0
            for p in places:
                if count >= data_per_city: break
                try:
                    name = p.get_attribute("aria-label")
                    
                    # Mencari elemen teks di sekitar (parent/sibling)
                    # Kita ambil teks dari elemen pembungkus yang lebih besar
                    parent_element = p.find_element(By.XPATH, "./../../..")
                    info_text = parent_element.text
                    
                    lines = info_text.split('\n')
                    
                    # 1. Ekstraksi RATING (Mencari pola angka seperti 4.5 atau 4,5)
                    rating = 0.0
                    for line in lines:
                        # Google Maps biasanya menulis: "4,5 (123)" atau "4.5 (123)"
                        if '(' in line and (',' in line or '.' in line):
                            potential_rating = line.split('(')[0].strip().replace(',', '.')
                            try:
                                rating = float(potential_rating)
                                if rating > 5.0: rating = 0.0 # Validasi
                                break
                            except: continue

                    # 2. Ekstraksi STATUS BUKA/TUTUP
                    status = "Tutup"
                    if "Buka" in info_text:
                        status = "Buka"
                    elif "Buka pukul" in info_text:
                        status = "Buka"

                    # 3. Ekstraksi JAM OPERASIONAL
                    jam = "Jam tidak tersedia"
                    for line in lines:
                        if "pukul" in line.lower() or "tutup" in line.lower() or "buka" in line.lower():
                            jam = line
                            break

                    if name and name not in [d['Nama'] for d in all_data]:
                        all_data.append({
                            "Nama": name,
                            "Kota": city,
                            "Kategori": random.choice(["Bakso", "Cafe", "Seblak", "Seafood", "Kopi", "Restoran"]),
                            "Rating": rating,
                            "Jam": jam,
                            "Status": status,
                            "lat": coords[0] + random.uniform(-0.04, 0.04),
                            "lng": coords[1] + random.uniform(-0.04, 0.04)
                        })
                        count += 1
                except: continue
            
            print(f"Berhasil mengambil {count} data dari {city}.")

        df_final = pd.DataFrame(all_data)
        # Pastikan kolom Rating benar-benar angka
        df_final['Rating'] = pd.to_numeric(df_final['Rating'], errors='coerce').fillna(0.0)
        df_final.to_csv("data_jabar_umkm.csv", index=False)
        driver.quit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    scrape_jabar_raya(10)
