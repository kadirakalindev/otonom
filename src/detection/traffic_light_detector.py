"""
Trafik Işığı Algılama Modülü
"""
import cv2
import numpy as np
from loguru import logger
from config.config import (
    TRAFIK_ISIGI_MIN_BOYUT,
    TRAFIK_ISIGI_MAX_BOYUT
)

class TrafficLightDetector:
    """Trafik ışığı algılama ve renk tespiti için sınıf."""
    
    def __init__(self):
        """Trafik ışığı algılama parametrelerini başlatır."""
        # Renk aralıkları (HSV)
        self.kirmizi_alt = np.array([0, 100, 100])
        self.kirmizi_ust = np.array([10, 255, 255])
        self.kirmizi_alt2 = np.array([170, 100, 100])
        self.kirmizi_ust2 = np.array([180, 255, 255])
        
        self.sari_alt = np.array([20, 100, 100])
        self.sari_ust = np.array([30, 255, 255])
        
        self.yesil_alt = np.array([40, 100, 100])
        self.yesil_ust = np.array([80, 255, 255])
        
        # Boyut sınırları
        self.min_boyut = TRAFIK_ISIGI_MIN_BOYUT
        self.max_boyut = TRAFIK_ISIGI_MAX_BOYUT
        
        logger.info("Trafik ışığı algılama sistemi başlatıldı")
    
    def _renk_maskesi_olustur(self, frame, alt_sinir, ust_sinir):
        """Belirli bir renk aralığı için maske oluşturur.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            alt_sinir (numpy.ndarray): HSV alt sınır değerleri
            ust_sinir (numpy.ndarray): HSV üst sınır değerleri
            
        Returns:
            numpy.ndarray: İkili maske görüntüsü
        """
        try:
            # BGR'den HSV'ye dönüşüm
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Renk maskesi
            mask = cv2.inRange(hsv, alt_sinir, ust_sinir)
            
            # Gürültü temizleme
            kernel = np.ones((3,3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            return mask
            
        except Exception as e:
            logger.error(f"Renk maskesi oluşturma hatası: {str(e)}")
            return None
    
    def _dairesel_nesne_bul(self, mask):
        """Maske üzerinde dairesel nesneleri tespit eder.
        
        Args:
            mask (numpy.ndarray): İkili maske görüntüsü
            
        Returns:
            list: Tespit edilen dairelerin merkez koordinatları ve yarıçapları
        """
        try:
            # Konturları bul
            konturlar, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            daireler = []
            for kontur in konturlar:
                # Kontur alanını kontrol et
                alan = cv2.contourArea(kontur)
                if alan < self.min_boyut[0] * self.min_boyut[1]:
                    continue
                
                # Çevrel dikdörtgen boyutlarını kontrol et
                x, y, w, h = cv2.boundingRect(kontur)
                if w > self.max_boyut[0] or h > self.max_boyut[1]:
                    continue
                
                # Dairesellik oranını kontrol et
                cevre = cv2.arcLength(kontur, True)
                if cevre == 0:
                    continue
                dairesellik = 4 * np.pi * alan / (cevre * cevre)
                
                if dairesellik > 0.7:  # Dairesellik eşiği
                    merkez = (int(x + w/2), int(y + h/2))
                    yaricap = int((w + h) / 4)
                    daireler.append((merkez, yaricap))
            
            return daireler
            
        except Exception as e:
            logger.error(f"Dairesel nesne bulma hatası: {str(e)}")
            return []
    
    def isik_durumunu_tespit_et(self, frame):
        """Trafik ışığının durumunu tespit eder.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            tuple: (durum, koordinatlar) - Işık durumu ve konumu
        """
        if frame is None:
            return None, None
            
        try:
            # Kırmızı ışık kontrolü
            kirmizi_mask1 = self._renk_maskesi_olustur(frame, self.kirmizi_alt, self.kirmizi_ust)
            kirmizi_mask2 = self._renk_maskesi_olustur(frame, self.kirmizi_alt2, self.kirmizi_ust2)
            if kirmizi_mask1 is not None and kirmizi_mask2 is not None:
                kirmizi_mask = cv2.bitwise_or(kirmizi_mask1, kirmizi_mask2)
                kirmizi_daireler = self._dairesel_nesne_bul(kirmizi_mask)
                if kirmizi_daireler:
                    return "kirmizi", kirmizi_daireler[0][0]
            
            # Sarı ışık kontrolü
            sari_mask = self._renk_maskesi_olustur(frame, self.sari_alt, self.sari_ust)
            if sari_mask is not None:
                sari_daireler = self._dairesel_nesne_bul(sari_mask)
                if sari_daireler:
                    return "sari", sari_daireler[0][0]
            
            # Yeşil ışık kontrolü
            yesil_mask = self._renk_maskesi_olustur(frame, self.yesil_alt, self.yesil_ust)
            if yesil_mask is not None:
                yesil_daireler = self._dairesel_nesne_bul(yesil_mask)
                if yesil_daireler:
                    return "yesil", yesil_daireler[0][0]
            
            return None, None
            
        except Exception as e:
            logger.error(f"Işık durumu tespit hatası: {str(e)}")
            return None, None
    
    def mesafe_tahmin_et(self, frame, koordinatlar):
        """Trafik ışığına olan mesafeyi piksel boyutuna göre tahmin eder.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            koordinatlar (tuple): Trafik ışığının merkez koordinatları
            
        Returns:
            float: Tahmini mesafe (cm)
        """
        if frame is None or koordinatlar is None:
            return float('inf')
            
        try:
            # Görüntü boyutları
            height, width = frame.shape[:2]
            
            # Trafik ışığının y koordinatı
            y = koordinatlar[1]
            
            # Basit bir mesafe tahmini (kalibre edilmeli)
            # Görüntünün üst kısmındaki ışıklar daha uzakta
            mesafe = 200 * (1 - y/height)  # 200cm maksimum mesafe varsayımı
            
            return max(0, mesafe)
            
        except Exception as e:
            logger.error(f"Mesafe tahmin hatası: {str(e)}")
            return float('inf') 