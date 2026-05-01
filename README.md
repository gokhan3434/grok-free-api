# Beykoz CBS Desktop Analiz

## Otomatik Token Bulma
Program artık tokenı otomatik bulmayı dener:
1. Base URL içeriğini tarar.
2. HTML/JS dosyalarında `X-Auth-Token`, `authToken`, `token` patternlerini regex ile arar.
3. Bulamazsa Token Endpoint çağırır.
4. Bulamazsa Token Command çalıştırır.
5. En sonda manual token kullanır.

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
Beykoz mahalleleri combobox içinde hazır gelir.
