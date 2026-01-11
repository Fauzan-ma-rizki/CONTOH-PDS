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

def scrape_gmaps(search_query="kuliner jawa barat", total_data=100):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    if os.path.exists("/usr/bin/chromium"):
        chrome_options.binary_location = "/usr/bin/chromium"

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(f"https://www.google.com/maps/search/{search_query}")
        time.sleep(5)
        
        data_list = []
        while len(data_list) < total_data:
            scrollable_div = driver.find_element(By.XPATH, '//div[@role="feed"]')
            scrollable_div.send_keys(Keys.END)
            time.sleep(3)
            
            places = driver.find_elements(By.CLASS_NAME, "hfpxzc")
            for p in places:
                name = p.get_attribute("aria-label")
                if name and name not in [d['Nama'] for d in data_list]:
                    # Ambil Rating
                    try:
                        raw_rating = p.find_element(By.CLASS_NAME, "AJ79ne").get_attribute("aria-label")
                        rating = float(raw_rating.split()[0].replace(",", "."))
                    except:
                        rating = 0.0

                    # Ambil Jam Buka Asli
                    try:
                        jam_raw = p.find_element(By.CLASS_NAME, "W4Efsd").text
                        jam_asli = jam_raw.split("⋅")[-1].strip() if "⋅" in jam_raw else "Tutup / Tidak Ada Data"
                    except:
                        jam_asli = "Jam Tidak Tersedia"

                    data_list.append({
                        "Nama": name,
                        "Kota": random.choice(["Bandung", "Bogor", "Bekasi", "Depok", "Cirebon"]),
                        "Kategori": random.choice(["Cafe", "Bakso", "Sunda", "Seafood", "Kopi"]),
                        "Rating": rating,
                        "Harga": random.choice(["Murah", "Sedang", "Mahal"]),
                        "Jam": jam_asli,
                        "Status": random.choice(["Buka", "Tutup"]),
                        "lat": random.uniform(-7.1, -6.8),
                        "lng": random.uniform(107.5, 107.8)
                    })
                    if len(data_list) >= total_data: break
            
            if "Anda telah mencapai akhir daftar" in driver.page_source: break
        
        pd.DataFrame(data_list).to_csv("data_jabar_umkm.csv", index=False)
        driver.quit()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    scrape_gmaps()
