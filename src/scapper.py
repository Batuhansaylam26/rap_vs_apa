# Selenium Kütüphaneleri
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraper:
    """Selenium WebDriver işlemlerini yönetir."""
    
    def __init__(self, url="https://rpachallenge.com"):
        print("WebScraper başlatılıyor...")
        self.url = url
        # Firefox ayarları
        options = Options()
        # options.add_argument("-headless") 
        self.driver = webdriver.Firefox(options=options)
        self.driver.maximize_window()
        self.wait = WebDriverWait(self.driver, 10) # 10 saniye bekleme süresi

    def setup_challenge(self):
        """Web sitesine gider ve başlangıç butonuna tıklar."""
        self.driver.get(self.url)

        # Butonun tıklanabilir olmasını bekle
        start_button = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, '//button'))
        )
        start_button.click()

    def get_labels(self):
        """Mevcut formdaki tüm etiketleri (label) okur."""
        self.setup_challenge()
        # Formun görünür olmasını bekle
        self.wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH, 
                    '//form'
                )
            )
        )
        
        divs = self.driver.find_elements(
            "xpath",
            '//form/div[@class="row"]/div'
        )
        labels = [d.text.strip() for d in divs]
        return labels

    def execute_fill_and_submit(self, plan: dict):
        """Formu doldurur ve gönderir."""
        
        # Etiketlere göre input alanlarını doldur
        for label, value in plan.items():
            # Label metnine göre input alanını bul
            input_field = self.driver.find_element(
                "xpath", 
                f'//label[contains(text(), "{label}")]/following-sibling::input'
            )
            #print(input_field)
            input_field.clear()
            # Değeri stringe çevirip gönder
            input_field.send_keys(str(value))


        # Gönder düğmesini bul ve tıkla
        submit_button = self.driver.find_element("xpath", '//form/input[@type="submit"]')
        submit_button.click()
        

        print(f"Form başarıyla gönderildi.")
        return True


    def quit(self):
        """WebDriver'ı kapatır."""
        if self.driver:
            self.driver.quit()
            print("WebDriver kapatıldı.")