# Beykoz CBS Desktop Analiz

Bu uygulama, Beykoz mahallelerinden ada/parsel sorgusu alıp CBS verisini çekmek, imar hesaplarını çıkarmak ve PDF rapor üretmek için tasarlanmıştır.

## Çalıştırma
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python desktop_app.py
```

## Token/API Yapısı (Detay)
Uygulama 3 farklı token kaynağını destekler:

1. **Manual X-Auth-Token**
   - Tarayıcı geliştirici araçlarından alınan token doğrudan girilir.
2. **Token Endpoint (opsiyonel)**
   - Eğer kurum tarafında token üreten bir endpoint varsa URL girilir.
   - `JSON Path` alanı ile response içindeki token yolu belirtilir (ör: `data.token`).
3. **Token Command (opsiyonel)**
   - Kurum içi script/komut token üretiyorsa (ör: SSO script), bu komut çalıştırılır ve stdout token kabul edilir.

Öncelik sırası: manual token > token endpoint > token command.

## Beykoz Mahalleleri
Uygulama içinde Beykoz mahalleleri combobox ile gelir; kullanıcı eksiksiz listeden seçip sorgu yapar.

## Build (indirilebilir tek dosya)
```bash
./build_desktop.sh
```
Çıktı:
- `dist/beykoz-cbs-desktop` (Linux)

## Hukuki Not
Veriler bilgilendirme amaçlıdır; resmi imar belgesi yerine geçmez.
