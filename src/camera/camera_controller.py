"""
Kamera Kontrol Modülü
"""
import cv2
import numpy as np
from picamera2 import Picamera2
from loguru import logger
from config.config import (
    KAMERA_COZUNURLUK,
    KAMERA_FPS,
    KAMERA_EXPOSURE
)

class CameraController:
    """Raspberry Pi Kamera kontrolü için sınıf."""
    
    def __init__(self):
        """Kamera ayarlarını başlatır."""
        try:
            self.camera = Picamera2()
            
            # Kamera konfigürasyonu
            config = self.camera.create_still_configuration(
                main={"size": KAMERA_COZUNURLUK},
                controls={"FrameRate": KAMERA_FPS,
                         "ExposureTime": KAMERA_EXPOSURE}
            )
            self.camera.configure(config)
            
            # Kamerayı başlat
            self.camera.start()
            
            logger.info("Kamera sistemi başlatıldı")
            
        except Exception as e:
            logger.error(f"Kamera başlatılamadı: {str(e)}")
            raise
    
    def capture_frame(self):
        """Kameradan bir kare yakalar ve numpy dizisi olarak döndürür.
        
        Returns:
            numpy.ndarray: BGR formatında görüntü verisi
        """
        try:
            frame = self.camera.capture_array()
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Kare yakalanamadı: {str(e)}")
            return None
    
    def apply_roi(self, frame, top_percent=60, bottom_percent=100):
        """Görüntüde ilgilenilen bölgeyi (ROI) belirler.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            top_percent (int): Üstten başlama yüzdesi
            bottom_percent (int): Alttan bitiş yüzdesi
            
        Returns:
            tuple: (roi_frame, (y_start, y_end)) - Kırpılmış görüntü ve koordinatlar
        """
        if frame is None:
            return None, (0, 0)
        
        height = frame.shape[0]
        y_start = int(height * top_percent / 100)
        y_end = int(height * bottom_percent / 100)
        
        return frame[y_start:y_end, :], (y_start, y_end)
    
    def preprocess_frame(self, frame):
        """Görüntüyü ön işlemden geçirir.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            numpy.ndarray: İşlenmiş görüntü
        """
        if frame is None:
            return None
            
        try:
            # Gürültü azaltma
            blurred = cv2.GaussianBlur(frame, (5, 5), 0)
            
            # Kontrast artırma
            lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            cl = clahe.apply(l)
            enhanced = cv2.merge((cl, a, b))
            
            return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
            
        except Exception as e:
            logger.error(f"Görüntü ön işleme hatası: {str(e)}")
            return frame
    
    def close(self):
        """Kamera sistemini kapatır."""
        try:
            self.camera.stop()
            logger.info("Kamera sistemi kapatıldı")
        except Exception as e:
            logger.error(f"Kamera kapatılırken hata: {str(e)}")
    
    def __del__(self):
        """Nesne silinirken kamerayı kapat."""
        self.close() 