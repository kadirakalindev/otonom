# Otonom Araç Geliştirme Projesi

## Proje Hakkında
Bu proje, Raspberry Pi 5 tabanlı bir otonom araç geliştirme projesidir. Araç, şerit takibi, trafik ışığı tanıma, şekil tabanlı tabela tespiti, güvenli sollama ve otonom park etme gibi temel otonom sürüş yeteneklerine sahiptir.

## Pist ve Araç Özellikleri
- Pist Genişliği: 100 cm
- Şerit Sayısı: 2 (Her biri 40 cm)
- Araç Boyutları: 20 cm x 30 cm
- Tabela Özellikleri:
  - Direk Yüksekliği: 20 cm
  - Tabela Yüksekliği: 13 cm
  - Toplam Yükseklik: 33 cm

## Donanım Gereksinimleri
- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- L298N Motor Sürücü
- DC Motorlar (2 adet, 280 rpm)
- Lipo Pil ve Voltaj Regülatörü
- Sarhoş Teker

## Kurulum

### 1. Sistem Güncellemesi
```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Gerekli Paketlerin Kurulumu
```bash
# Python ve geliştirme araçları
sudo apt install -y python3-pip python3-dev
sudo apt install -y python3-picamera2

# OpenCV bağımlılıkları
sudo apt install -y build-essential cmake pkg-config
sudo apt install -y libjpeg-dev libtiff5-dev libjasper-dev libpng-dev
sudo apt install -y libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt install -y libxvidcore-dev libx264-dev
sudo apt install -y libfontconfig1-dev libcairo2-dev
sudo apt install -y libgdk-pixbuf2.0-dev libpango1.0-dev
sudo apt install -y libgtk2.0-dev libgtk-3-dev
sudo apt install -y libatlas-base-dev gfortran
```

### 3. Virtual Environment Kurulumu
```bash
# virtualenv kurulumu
sudo pip3 install virtualenv

# Proje klasörüne git
cd /home/pi/otonom

# Virtual environment oluştur
python3 -m venv env

# Virtual environment'ı aktif et
source env/bin/activate
```

### 4. Python Paketlerinin Kurulumu
```bash
# pip'i güncelle
pip install --upgrade pip

# Gerekli paketleri yükle
pip install -r requirements.txt
```

### 5. GPIO ve Kamera Ayarları
```bash
# GPIO izinleri
sudo usermod -a -G gpio $USER

# Kamera arayüzünü etkinleştir
sudo raspi-config
# Interface Options -> Camera -> Enable seçin
```

### 6. Log Klasörü Oluşturma
```bash
mkdir -p logs
```

## Kalibrasyon

### Kamera Kalibrasyonu
1. Kalibrasyon aracını başlatın:
```bash
# Virtual environment'ı aktif et (eğer aktif değilse)
source env/bin/activate

# Kalibrasyon aracını çalıştır
python -m src.utils.calibration_tool
```

2. Kalibrasyon İşlemi:
- 'c' tuşu: Yeniden kalibrasyon başlatır
- 's' tuşu: Kalibrasyon görüntülerini kaydeder
- 'q' tuşu: Programdan çıkar

3. Kalibrasyon İpuçları:
- Kamerayı pistin üzerinde 30-40 cm yükseklikte konumlandırın
- Pist çizgilerinin net görünmesini sağlayın
- Işık yansımalarını önleyin
- Kalibrasyon noktalarını pist şeritlerine göre ayarlayın

### Tabela Tespiti Kalibrasyonu
1. Tabela tespit parametrelerini ayarlayın:
```python
detector = SignDetector(
    kamera_cozunurluk=(640, 480),
    min_alan_oran=0.01,
    max_alan_oran=0.1
)

# Canny ve diğer parametreleri ayarla
detector.parametreleri_ayarla(
    blur_kernel=(5,5),
    canny_alt=50,
    canny_ust=150,
    epsilon_oran=0.04,
    dairesellik_esik=0.8
)
```

## Programı Çalıştırma

### Manuel Çalıştırma
```bash
# Virtual environment'ı aktif et
source env/bin/activate

# Programı çalıştır
python -m src
```

### Otomatik Başlatma Servisi
1. Servis dosyası oluşturun:
```bash
sudo nano /etc/systemd/system/otonom.service
```

2. Aşağıdaki içeriği ekleyin:
```ini
[Unit]
Description=Otonom Araç Servisi
After=multi-user.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/otonom
ExecStart=/home/pi/otonom/env/bin/python3 -m src
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Servisi etkinleştirin:
```bash
sudo systemctl enable otonom
sudo systemctl start otonom
```

4. Servis durumunu kontrol edin:
```bash
sudo systemctl status otonom
```

## Hata Ayıklama

### Log Dosyaları
- Ana program logları: `logs/otonom_arac.log`
- Kalibrasyon logları: `logs/kalibrasyon.log`

### Sık Karşılaşılan Sorunlar
1. Kamera Hatası:
```bash
# Kamera servisini yeniden başlat
sudo systemctl restart camera.service
```

2. GPIO Hatası:
```bash
# GPIO'ları sıfırla
sudo gpioset --mode=time -u 100 gpiochip0 17=0 18=0 22=0 23=0
```

3. Performans Sorunları:
```bash
# CPU frekansını maksimuma çıkar
echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## Proje Yapısı
```
otonom/
├── src/                    # Kaynak kodlar
│   ├── camera/            # Kamera ve görüntü işleme
│   ├── control/           # Motor kontrolü ve hareket
│   ├── detection/         # Nesne tespiti ve tanıma
│   ├── utils/             # Yardımcı fonksiyonlar
│   └── __main__.py        # Ana program
├── config/                # Yapılandırma dosyaları
├── tests/                 # Test dosyaları
├── logs/                  # Log dosyaları
└── requirements.txt       # Python bağımlılıkları
```

## Lisans
MIT License 