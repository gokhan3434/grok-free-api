# İlan Toplayıcı

Sahibinden.com üzerindeki kendi oturumunuzu kullanarak manuel olarak erişebildiğiniz ilanları masaüstü üzerinden toplayan PySide6 + Playwright uygulaması.

## Özellikler
- Kendi Chrome/Edge oturumunuzu **kullanır**, e-posta/şifre istemez.
- Listeleme sayfalarından ilan kartlarını okur, isteğe bağlı detay sayfasına girerek alanları çıkartır.
- İlerleme ve logları canlı olarak gösterir; aynı ilanı iki kez işlemez.
- Verileri Excel, CSV veya JSON olarak dışa aktarır.
- Qt tabanlı masaüstü arayüz; scraping işlemi ayrı iş parçacığında çalışır.

## Kurulum
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m playwright install chrome
```

## Çalıştırma
```bash
python main.py
```

> İpucu: Açık olan Chrome/Edge oturumunuzdaki çerezi kullanmak için tarayıcıyı `--remote-debugging-port=9222` ile başlatıp ortam değişkeni `REMOTE_DEBUG_URL=http://localhost:9222` verebilirsiniz. Aksi halde Playwright kalıcı profil klasörü `.ilan_toplayici/profile` altında tutulur ve ilk açılışta manuel giriş yapabilirsiniz.

## Paketleme (PyInstaller)
```bash
pyinstaller build.spec
```
Tek dosya exe çıktısı `dist/` klasöründe oluşur.

## UI Akışı
1. Kullanıcı sahibinden.com'a kendi tarayıcısıyla giriş yapar.
2. "Listeleme URL" alanına filtreli ilan listesini yapıştırır; sayfa sayısı ve gecikme değerlerini belirler.
3. "Başlat" ile tarama sürecini izler; dilerse "Durdur" ile temiz şekilde kapatır.
4. Tablo güncellenen ilan satırlarını gösterir; alt bölümde sayaçlar ve log akışı bulunur.
5. Excel/CSV/JSON butonlarıyla sonuçlar dışa aktarılır.

## Hata Senaryoları ve Log Örnekleri
- Ağ veya selector hatası: `Kritik hata: TimeoutError` gibi satırlar log penceresinde gösterilir, süreç diğer ilanlarla devam eder.
- İlan detayında telefon görünmezse: satır "Telefon" kolonunda boş kalır, istenirse "Sadece iletişim" filtresiyle elenir.
- Sonraki sayfa tıklama sorunları: `Sonraki sayfaya geçerken hata: ...` mesajı loga düşer.

## Dosya Yapısı
```
/ilan_toplayici
  /app
    main.py         # Qt uygulama giriş noktası
    ui_main.py      # UI düzeni ve model
    scraper.py      # Playwright QThread işçisi
    parser.py       # Selector bazlı alan çıkarma
    exporter.py     # Excel/CSV/JSON dışa aktarım
    storage.py      # In-memory + sqlite cache
    models.py       # Veri modelleri
    utils.py        # Yardımcı araçlar
  requirements.txt
  README.md
  build.spec
  assets/
```
