#!/bin/bash

# 1. Sistemi güncelle
sudo apt-get update && sudo apt-get upgrade -y

# 2. Python ve Sanal Ortam araçlarını kur
sudo apt-get install python3-pip python3-venv -y

# 3. Proje klasörüne git ve sanal ortam oluştur
cd /home/ubuntu/geo-spatial-scraper
python3 -m venv venv
source venv/bin/activate

# 4. Python kütüphanelerini yükle
pip install --upgrade pip
pip install -r requirements.txt

# 5. Playwright sistem bağımlılıklarını otomatik kur (En kritik adım)
playwright install --with-deps chromium

print("Oracle VM Kurulumu Başarıyla Tamamlandı!")