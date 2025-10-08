# WhatsApp Otomasyon Servisi

Bu proje, WhatsApp kod ile giriş yapabileceğiniz ve toplu/tekil mesaj gönderebileceğiniz bir FastAPI servisi sağlar. CSV ile yüklenen telefon numaraları otomatik olarak normalize edilir ve tekrar eden kayıtlar atlanır. Servis, WhatsApp Cloud API'yi kullanarak metin, görsel ve belge paylaşımını destekler.

## Özellikler

- 🔐 Kod ile giriş ve oturum yönetimi (6 haneli doğrulama kodu)
- 📁 CSV yükleyerek kişi listesi oluşturma, numaraları normalize etme ve yinelenenleri raporlama
- 💬 Tek seferde bir veya birden fazla kişiye metin mesajı gönderme
- 🖼️ Görsel ve 📄 belge paylaşımı (WhatsApp Cloud API üzerinden herkese açık bağlantılarla)
- 🧾 Başarılı, başarısız ve atlanan numaralar için detaylı işlem raporu

## Kurulum

1. Depoyu klonlayın ve bağımlılıkları yükleyin:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. Ortam değişkenlerini ayarlayın:

   ```bash
   export WHATSAPP_PHONE_NUMBER_ID="<Meta Cloud API telefon numarası ID'niz>"
   export WHATSAPP_ACCESS_TOKEN="<Uzun ömürlü erişim token'ınız>"
   ```

   > **Not:** WhatsApp Cloud API kullanmak için Meta geliştirici hesabına ihtiyacınız vardır. Belirtilen değişkenler ayarlanmadığında mesaj gönderme isteği hata döndürür.

3. Uygulamayı başlatın:

   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8046 --reload
   ```

## API Kullanımı

### 1. Doğrulama kodu isteyin

`POST /auth/request-code`

```json
{
  "phone_number": "+905321112233"
}
```

> Geliştirme ortamında kod JSON cevabında döner. Üretim için bu kodu SMS veya WhatsApp üzerinden manuel olarak göndermeniz önerilir.

### 2. Kodu doğrulayarak oturum açın

`POST /auth/verify-code`

```json
{
  "phone_number": "+905321112233",
  "verification_code": "123456"
}
```

Cevaptaki `session_token` değerini sonraki isteklerde `X-Session-Token` başlığı olarak kullanın.

### 3. CSV ile kişiler yükleyin

`POST /contacts/upload`

- İçerik tipi: `multipart/form-data`
- Parametre: `file` (CSV dosyası)

CSV dosyasında `phone`, `phone_number`, `number`, `msisdn` veya `tel` başlığı olan bir sütun bulunmalıdır.

### 4. Mesaj gönderme uç noktaları

Tüm isteklerde `X-Session-Token` başlığı zorunludur.

- `POST /messages/send-text` – `message` ve `recipients` alanlarını içeren JSON gövdesi bekler.
- `POST /messages/send-image` – `link` (herkese açık görsel URL'si) ve isteğe bağlı `caption` bekler.
- `POST /messages/send-document` – `link`, isteğe bağlı `filename` ve `caption` alanlarını bekler.

`recipients` alanı tek bir numara (`"+9053..."`) veya numara listesi (`["+9053...", "+447..." ]`) olabilir. Servis numaraları normalize eder, yinelenenleri otomatik olarak atlar ve sonuçları raporlar.

## Test

Sunucunun sentaks hatası olmadan çalıştığından emin olmak için:

```bash
python -m compileall .
```

## Lisans

Bu proje MIT lisansı ile lisanslanmıştır.
