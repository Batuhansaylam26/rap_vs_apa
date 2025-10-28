from state import APAState
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import re # JSON temizliği için düzenli ifadeler
import json
from scapper import WebScraper
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())


scraper = WebScraper() 

def load_data_node(state: APAState):
    """Excel verisini yükler ve ilk durumu başlatır."""
    df = pd.read_excel("./data/challenge.xlsx")
    # Sütun başlıklarını temizle
    df.columns = [col.strip() for col in df.columns]

    print(f"Excel'den {len(df)} satır veri yüklendi.")
    
    # WebDriver'ı başlat ve challenge'ı kur
    
    scraper.setup_challenge()

    return {
        "df": df,
        "max_rows": len(df),
        "current_row_index": 0,
        "error_message": ""
    }

def get_labels_node(state: APAState):
    """Selenium kullanarak web formundan etiketleri okur."""
    print(f"\n--- Satır {state['current_row_index'] + 1} için form etiketleri okunuyor. ---")
    
    try:
        labels = scraper.get_labels()
        if not labels:
            print("UYARI: Hiç form etiketi bulunamadı. Muhtemelen challenge bitti.")
            # Challenge bitmişse, döngüyü sonlandırmak için bir sonraki adıma hazırla
            return {
                "form_labels": [],
                "error_message": ""
            }
        
        # Etiketleri güncel duruma kaydet
        return {
            "form_labels": labels,
            "error_message": ""
        }
        
    except Exception as e:
        print(f"HATA: Etiket okuma başarısız oldu: {e}")
        return {
            "error_message": f"Etiket okuma hatası: {e}"
        }

def decide_fill_plan_node(state: APAState):
    """
    LLM Agent (Gemini) kullanarak form doldurma planını (Excel verisi -> Form alanı eşleşmesi) oluşturur.
    Agentic yapının kalbi burasıdır, karar alma mekanizmasıdır.
    """
    
    # Eğer form etiketi yoksa (get_labels_node'da başarısız olduysa), boş plan döndür.
    if not state["form_labels"]:
        return {"current_plan": {}, "error_message": ""}
        
    current_row = state["df"].iloc[state["current_row_index"]]
    labels = state["form_labels"]
    
    # Modelin rolünü tanımlayan sistem mesajı (Türkçe)
    system_msg = """
    Sen bir yardımcı asistansın. Görevin, verilen web form etiketlerine göre, Excel satırındaki hangi değerin nereye yazılacağını belirlemektir.
    Cevabını **KESİNLİKLE** sadece ve sadece JSON formatında ver. JSON bloğunun dışına hiçbir açıklama veya metin ekleme. JSON anahtarları tam olarak form etiketleri olmalı, değerleri ise Excel satırındaki karşılık gelen değerler olmalıdır.
    Eğer form etiketinde karşılık gelen bir Excel sütunu (anahtarı) bulamazsan, o alana boşluk ("") değeri ata.
    """
    
    # Kullanıcıya gönderilecek prompt
    user_prompt = f"""
    Form etiketleri: {labels}
    Excel satırı (Anahtar: Değer): {current_row.to_dict()}
    """
    
    # LLM Modeli
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-preview-09-2025", 
        temperature=0.0
    )
    
    messages = [
        ("system",system_msg),
        ("human", user_prompt)
    ]

    print("Gemini Agent'tan doldurma planı bekleniyor...")
    
    try:
        # LLM çağrısı
        response = llm.invoke(messages)
        plan_text = response.content.strip().replace("```json", "").replace("```", "").strip()

        # JSON'ı güvenli bir şekilde ayrıştır
        plan = json.loads(plan_text)
        print("Plan başarılı: ", plan)
        
        return {
            "current_plan": plan,
            "error_message": ""
        }
    except Exception as e:
        print(f"HATA: LLM çağrısı veya JSON ayrıştırma başarısız oldu. Çıktı: {plan_text[:100]}... Hata: {e}")
        return {
            "error_message": f"LLM veya JSON hatası: {e}"
        }


def execute_fill_node(state: APAState):
    """Oluşturulan planı Selenium ile web formuna uygular ve gönderir."""
    plan = state["current_plan"]
    #print(plan)
    
    # Eğer boş bir plan gelirse, bir sonraki adıma geçmeden döngüyü kontrol et.
    if not plan:
        return {
            "current_row_index": state["current_row_index"] + 1,
            "error_message": ""
        }
    


    try:
        success = scraper.execute_fill_and_submit(plan)
        
        if success:
            # Başarılı ise bir sonraki satıra geç
            return {
                "current_row_index": state["current_row_index"] + 1,
                "error_message": ""
            }
        else:
            return {
                "error_message": "Form doldurma/gönderme hatası. İşlem durduruluyor."
            }
            
    except Exception as e:
        print(f"HATA: Form doldurma aşamasında kritik hata: {e}")
        return {
            "error_message": f"Kritik doldurma hatası: {e}"
        }


def is_finished_node(state: APAState) -> str:
    """Tüm satırlar işlendi mi veya form etiketleri boş mu kontrol eder."""
    # Hata oluştuysa sonlandır
    if state["error_message"]:
        scraper.quit()
        print(f"HATA NEDENİYLE DURDURULDU: {state['error_message']}")
        return "end_with_error"
        
    # Tüm satırlar işlendiyse sonlandır
    if state["current_row_index"] >= state["max_rows"]:
        print("Tüm satırlar işlendi. İş akışı sonlandırılıyor.")
        scraper.quit()
        return "finished"
        
    # Eğer form etiketleri boş geldiyse (genellikle challenge bittiğinde olur), sonlandır.
    if state["current_row_index"] > 0 and not state["form_labels"]:
        print("Web formundan etiket gelmedi. İş akışı tamamlandı kabul ediliyor.")
        scraper.quit()
        return "finished"
        
    # Devam et
    print(f"İşlenmesi gereken {state['max_rows'] - state['current_row_index']} satır kaldı.")
    return "continue"