# Grok Free API & Sahibinden Scraper Toolkit

This repository now contains two separate utilities:

1. **FastAPI proxy** (existing `main.py`) – demonstrates how to proxy requests to xAI's Grok API.
2. **Sahibinden.com real-estate scraper GUI** – a Tkinter-based desktop client that can collect
   property listings from sahibinden.com, filter them, and export the results to Excel/CSV.

## Sahibinden Scraper

> ⚠️ **Yasal Uyarı:** Sahibinden.com'dan veri çekerken mutlaka kullanım şartlarını ve ilgili
> mevzuatı inceleyin. `robots.txt` dosyasına uyun, aşırı istek göndermeyin ve kişisel verilerin
> korunmasına dikkat edin. Bu proje yalnızca eğitim amaçlıdır; sorumluluk kullanıcıya aittir.

### Özellikler

- Konum, fiyat, oda sayısı, metrekare vb. filtrelerle ilan arama.
- Sayfa bazlı veri çekme ve maksimum ilan limiti.
- Acil veya istenmeyen anahtar kelimeleri hariç tutma.
- BeautifulSoup tabanlı HTML ayrıştırma, isteğe bağlı proxy/headless tarayıcı desteği için hazır yapı.
- Pandas DataFrame olarak veri işleme, duplikasyonları filtreleme.
- Excel (`.xlsx`) veya CSV olarak dışa aktarma.
- Tkinter arayüzü (filtre girişleri, arama butonu, ilerleme çubuğu, sonuç tablosu).
- Günlük (log) dosyası oluşturma ve site yapısı değiştiğinde anlamlı hatalar verme.

### Kurulum

```bash
python -m venv .venv
source .venv/bin/activate  # Windows için .venv\\Scripts\\activate
pip install -r requirements.txt
```

Selenium ile headless tarayıcı kullanmak isterseniz sisteminizde uygun bir WebDriver (örneğin
`chromedriver`) bulunmalıdır.

### Kullanım

```bash
python -m sahibinden_scraper.gui
```

1. Filtreleri doldurun ve "İlanları Ara" butonuna basın.
2. İsterseniz çıktı klasörünü değiştirin ve maksimum ilan sayısını ayarlayın.
3. Liste dolduktan sonra "Excel'e Aktar" ile verileri `exports/` klasörüne kaydedin.

Log dosyası varsayılan olarak `logs/scraper.log` konumunda tutulur.

## Mevcut FastAPI Uygulaması

```
uvicorn main:app --reload
```

Bu uygulama, Grok API isteği yapabilmek için gerekli çerezleri (`cookies`) `main.py` dosyasında
belirtmenizi gerektirir.

## Lisans

Bu projede kullanılan tüm üçüncü parti kütüphaneler açık kaynaklıdır. Kodlar eğitim amaçlı olup,
her türlü kullanım sorumluluğu kullanıcıya aittir.
