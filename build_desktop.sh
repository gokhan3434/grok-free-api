#!/usr/bin/env bash
set -euo pipefail
python -m pip install -r requirements.txt
pyinstaller --noconfirm --onefile --name beykoz-cbs-desktop desktop_app.py
echo "Build tamamlandi: dist/beykoz-cbs-desktop"
