"""
Sistem Konfigürasyon Dosyası
"""

# Pist ve Araç Boyutları (cm)
PIST_GENISLIK = 100
SERIT_GENISLIK = 40
ARAC_GENISLIK = 20
ARAC_UZUNLUK = 30

# Motor Pin Konfigürasyonu (BCM)
MOTOR_SOL_ILERI = 17
MOTOR_SOL_GERI = 18
MOTOR_SAG_ILERI = 22
MOTOR_SAG_GERI = 23
MOTOR_SOL_PWM = 19
MOTOR_SAG_PWM = 24

# Motor Hız Ayarları
MAX_PWM = 100  # Maximum PWM değeri
MIN_PWM = 0    # Minimum PWM değeri
BASLANGIC_HIZI = 50  # Başlangıç PWM değeri

# Kamera Ayarları
KAMERA_COZUNURLUK = (640, 480)
KAMERA_FPS = 30
KAMERA_EXPOSURE = 'auto'

# Görüntü İşleme Parametreleri
SERIT_HSV_ALT = (0, 0, 200)  # Beyaz şerit için HSV alt sınır
SERIT_HSV_UST = (180, 30, 255)  # Beyaz şerit için HSV üst sınır

# Nesne Tanıma Parametreleri
TRAFIK_ISIGI_MIN_BOYUT = (20, 40)  # piksel
TRAFIK_ISIGI_MAX_BOYUT = (100, 200)  # piksel

# Mesafe ve Güvenlik Parametreleri
MIN_DURMA_MESAFESI = 50  # cm (trafik ışığı için)
YAYA_GECIDI_DURMA_MESAFESI = 30  # cm
SOLLAMA_MIN_MESAFE = 150  # cm
PARK_YERI_MIN_GENISLIK = 30  # cm
PARK_YERI_MIN_DERINLIK = 40  # cm

# Zaman Parametreleri
YAYA_GECIDI_BEKLEME_SURESI = 5  # saniye
HEMZEMIN_GECIT_BEKLEME_SURESI = 5  # saniye

# Log Ayarları
LOG_DOSYA = "logs/otonom_arac.log"
LOG_SEVIYESI = "INFO"

# Park Yeri Renk Kodları (BGR)
PARK_YERI_RENKLER = {
    'kirmizi': ([0, 0, 100], [80, 80, 255]),  # BGR alt ve üst sınırlar
    'mavi': ([100, 0, 0], [255, 80, 80]),
    'yesil': ([0, 100, 0], [80, 255, 80])
} 