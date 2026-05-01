# Beykoz CBS Desktop Analiz

Bu sürüm doğrudan **https://cbs.beykoz.bel.tr/** için ayarlıdır.

## Beykoz sitesi için otomatik token akışı
Program sırasıyla şunları dener:
1. `https://cbs.beykoz.bel.tr/` ana sayfa ve script taraması
2. `GiSoftGis/` alt yolu ve script taraması
3. Olası token endpoint denemeleri:
   - `/GiSoftGis/rest/auth/token`
   - `/GiSoftGis/rest/token`
   - `/GiSoftGis/api/token`
   - `/rest/auth/token`
4. Sonra opsiyonel Token Endpoint alanı
5. Sonra Token Command
6. En son Manual Token

## Çalıştırma
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python desktop_app.py
```

## Build
```bash
./build_desktop.sh
```

## Not
- Uygulama başlangıçta Beykoz adresleri ile hazır gelir.
- Mahalle listesi içinden seçim yapıp ada/parsel sorgulayabilirsiniz.
