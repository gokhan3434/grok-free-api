# Grok Free API + WhatsApp Tarzı Otomasyon Arayüzü

Yapay zekâ destekli WhatsApp benzeri otomatik karşılama ve mesaj yanıt otomasyonunu içeren FastAPI projesi.

## Kurulum
1) `main.py` içindeki `cookies` sözlüğüne Grok çerezlerinizi girin (opsiyonel, girmezseniz yerleşik offline cevaplayıcı kullanılır).
2) Bağımlılıkları kurun:
```bash
uv venv
uv pip install -r requirements.txt
```
3) İsterseniz Grok istemcisini ekleyin:
```bash
git clone https://github.com/mem0ai/grok3-api.git
cd ./grok3-api
uv pip install .
cd ..
```
4) Sunucuyu çalıştırın:
```bash
python main.py
```
5) Arayüz: `http://127.0.0.1:8046/`
6) API uç noktası: `http://127.0.0.1:8046/v1`

## Özellikler
- WhatsApp benzeri web arayüzü
- Yeni kullanıcılar için karşılama mesajı
- Mesai saatleri ve hafta sonu kontrolü
- Acil talep / eskalasyon akışı
- Hızlı yanıt butonları ve intent listesi
- Grok modeliyle AI yanıtları veya çevrimdışı fallback
