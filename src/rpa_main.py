import pandas as pd 
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from openpyxl import Workbook
from datetime import datetime
import re

data = pd.read_excel('data/challenge.xlsx')
data.columns = [col.strip() for col in data.columns]  # Sütun adlarındaki boşlukları temizleme
# Firefox için seçenekler
options = Options()
#options.add_argument("--headless")  # Başsız mod (görünmez)
options.binary_location = "/Applications/Firefox.app/Contents/MacOS/firefox"  # Firefox'un yolu

# Geckodriver servis yolu
service = Service("/opt/homebrew/bin/geckodriver") # Geckodriver'ın yolu

# WebDriver başlat
driver = webdriver.Firefox(service=service, options=options) # Firefox WebDriver'ı başlatma

start_time = time.time()  # Başlangıç zamanını kaydetme
driver.get("https://rpachallenge.com")
driver.maximize_window() # Pencereyi maksimize etme
driver.find_element("xpath", '//button').click() # Herhangi bir butona tıklama

for index, row in data.iterrows():
    #print(row)
    divs_rows =driver.find_elements("xpath",'//form/div[@class="row"]/div')  #divleri bulma
    for i in range(len(divs_rows)):
        input_section = divs_rows[i].find_element("xpath",'.//input') # İlgili input alanını bulma
        #print(divs_rows[i].text)
        #print(row[divs_rows[i].text])
        input_section.send_keys(
            row[divs_rows[i].text] # Veriyi ilgili input alanına gönderme
        )
    driver.find_element("xpath",'//form/input[@class="btn uiColorButton"]').click() # Submit butonuna tıklama
end_time = time.time()  # Bitiş zamanını kaydetme
total_time = end_time - start_time  # Toplam süreyi hesaplama
print(f"Toplam süre: {total_time} saniye")  # Toplam süreyi yazdırma
wait = WebDriverWait(driver, 10)
result_element = wait.until(
    EC.presence_of_element_located((By.XPATH, "//div[@class='message2']"))
)
print(result_element)
result_text = result_element.text
print("Sonuç Mesajı:", result_text)


match = re.search(r"(\d+)%.*\(\s*(\d+)\s*out of\s*\d+\s*fields\).*in\s*(\d+)\s*milliseconds", result_text)
if match:
    success_rate = int(match.group(1))        # % -> int
    filled_fields = int(match.group(2))       # doldurulan alan -> int
    duration_ms = int(match.group(3))         # süre -> int
else:
    success_rate = filled_fields = duration_ms = None

# --- 5. Excel dosyasını sıfırdan oluştur ---
wb = Workbook()
ws = wb.active
ws.title = "RPA Results"

# Başlık satırı
ws.append(["Tarih", "Başarı Oranı (%)", "Doldurulan Alan Sayısı", "Süre (ms)"])

# Veri satırı
ws.append([
    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    success_rate,
    filled_fields,
    duration_ms
])

# --- 6. Dosyayı kaydet ---
excel_path = "./output/results.xlsx"
wb.save(excel_path)
print(f"Sonuçlar kaydedildi: {excel_path}")
#driver.quit()  # Tarayıcıyı kapatma