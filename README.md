# eBird Hotspot Gözlem Sorgulayıcı (Streamlit UI)

Bu araç, eBird API v2.0 kullanarak belirli bir **Hotspot (Sıcak Nokta)** üzerinde, istediğiniz bir kuş türünün son 30 gün içindeki kayıtlarını modern bir web arayüzü ile sunar.

## Özellikler

- **Modern Web Arayüzü:** Streamlit ile geliştirilmiş, kullanıcı dostu arayüz.
- **Güvenli API Yönetimi:** API anahtarınızı uygulama içinden şifreli şekilde girebilirsiniz.
- **Görselleştirme:** `Metric` kartları ve `Expander` panelleri ile zengin veri sunumu.
- **Hızlı Önbellekleme:** Tür aramaları ve taksonomi verileri daha hızlı yanıt için önbelleğe alınır.

## Kurulum

1.  **Bağımlılıkları Yükleyin:**
    ```bash
    pip3 install -r requirements.txt
    ```

2.  **API Anahtarını Ayarlayın:**
    - `.env.example` dosyasının adını `.env` yapın ve anahtarınızı ekleyin (veya uygulama açıldığında kenar çubuğuna yazın).

## Kullanım

Uygulamayı başlatmak için:
```bash
streamlit run app.py
```

Tarayıcınızda otomatik olarak açılacaktır (genellikle `http://localhost:8501`).

## Teknik Detaylar

- **Dil:** Python 3.x
- **Kütüphaneler:** `streamlit`, `requests`, `python-dotenv`
- **Veri Kaynağı:** eBird API v2.0
