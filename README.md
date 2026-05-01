# Beykoz CBS Desktop Analiz (MVP)

Bu repo artık iki parçadan oluşur:
- `main.py`: Mevcut FastAPI servisi.
- `desktop_app.py`: Ada/parsel ile CBS sorgulayıp analiz ve PDF raporu üreten masaüstü uygulama.

## Hızlı Başlatma (Desktop)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python desktop_app.py
```

## Tek Tık Çalıştırılabilir Dosya Üretme

```bash
./build_desktop.sh
```

Çıktı:
- `dist/beykoz-cbs-desktop` (Linux tek dosya executable)

> Not: Windows için `.exe` üretimi Windows ortamında PyInstaller ile yapılmalıdır.

## Kullanım
1. `CBS Endpoint Template` alanına endpoint şablonu girin.
2. Gerekirse `X-Auth-Token` girin.
3. İlçe/Mahalle/Ada/Parsel girip **Sorgula + Analiz** tıklayın.
4. Sonuçları inceledikten sonra **PDF Oluştur** ile raporu `reports/` klasörüne alın.

## Hukuki Uyarı
Uygulama içindeki çıktılar bilgilendirme amaçlıdır, resmi belge yerine geçmez.
