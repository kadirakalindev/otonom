# Otonom Araç Geliştirme Projesi

## Proje Hakkında
Bu proje, Raspberry Pi 5 tabanlı bir otonom araç geliştirme projesidir. Araç, şerit takibi, trafik ışığı tanıma, nesne tespiti, güvenli sollama ve otonom park etme gibi temel otonom sürüş yeteneklerine sahiptir.

## Pist ve Araç Özellikleri
- Pist Genişliği: 100 cm
- Şerit Sayısı: 2 (Her biri 40 cm)
- Araç Boyutları: 20 cm x 30 cm

## Donanım Gereksinimleri
- Raspberry Pi 5
- Raspberry Pi Camera Module 3
- L298N Motor Sürücü
- DC Motorlar (2 adet, 280 rpm)
- Lipo Pil ve Voltaj Regülatörü
- Sarhoş Teker

## Kurulum
1. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

2. Raspberry Pi GPIO ve Kamera ayarlarını yapın:
```bash
sudo raspi-config
# Interface Options -> Camera -> Enable
# Interface Options -> I2C -> Enable
```

## Proje Yapısı
```
otonom/
├── src/                    # Kaynak kodlar
│   ├── camera/            # Kamera ve görüntü işleme
│   ├── control/           # Motor kontrolü ve hareket
│   ├── detection/         # Nesne tespiti ve tanıma
│   ├── navigation/        # Navigasyon ve rota planlaması
│   └── utils/             # Yardımcı fonksiyonlar
├── config/                # Yapılandırma dosyaları
├── tests/                 # Test dosyaları
└── logs/                  # Log dosyaları
```

## Lisans
MIT License 