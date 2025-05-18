"""
Ana Araç Kontrol Modülü
"""
import time
from loguru import logger
from config.config import (
    MIN_DURMA_MESAFESI,
    YAYA_GECIDI_DURMA_MESAFESI,
    YAYA_GECIDI_BEKLEME_SURESI,
    SOLLAMA_MIN_MESAFE
)
from src.camera.camera_controller import CameraController
from src.control.motor_controller import MotorController
from src.detection.lane_detector import LaneDetector
from src.detection.traffic_light_detector import TrafficLightDetector

class VehicleController:
    """Ana araç kontrol sınıfı."""
    
    def __init__(self):
        """Tüm alt sistemleri başlatır."""
        try:
            # Alt sistemleri başlat
            self.camera = CameraController()
            self.motors = MotorController()
            self.lane_detector = LaneDetector()
            self.traffic_light_detector = TrafficLightDetector()
            
            # Durum değişkenleri
            self.durum = "hazir"  # hazir, hareket, durma, sollama, park
            self.son_trafik_isigi = None
            self.bekleme_baslangic = None
            
            logger.info("Araç kontrol sistemi başlatıldı")
            
        except Exception as e:
            logger.error(f"Araç kontrol sistemi başlatılamadı: {str(e)}")
            self.temizle()
            raise
    
    def _serit_takibi(self, merkez_sapma):
        """Şerit takibi için motor kontrolü yapar.
        
        Args:
            merkez_sapma (float): Şerit merkezinden sapma miktarı (piksel)
        """
        try:
            # PID kontrol parametreleri (deneysel olarak ayarlanmalı)
            Kp = 0.5  # Oransal kazanç
            Ki = 0.1  # İntegral kazanç
            Kd = 0.2  # Türevsel kazanç
            
            # Temel hız
            temel_hiz = 50
            
            # Sapma miktarına göre motor hızlarını ayarla
            sapma_duzeltme = Kp * merkez_sapma
            
            sol_hiz = temel_hiz - sapma_duzeltme
            sag_hiz = temel_hiz + sapma_duzeltme
            
            # Hızları uygula
            self.motors.hiz_ayarla(sol_hiz, sag_hiz)
            
        except Exception as e:
            logger.error(f"Şerit takibi hatası: {str(e)}")
            self.motors.dur()
    
    def _trafik_isigi_kontrolu(self, frame):
        """Trafik ışığı durumunu kontrol eder ve gerekli aksiyonu alır.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            bool: Devam edilip edilmeyeceği
        """
        try:
            # Trafik ışığı durumunu al
            isik_durumu, koordinatlar = self.traffic_light_detector.isik_durumunu_tespit_et(frame)
            
            if isik_durumu is not None:
                # Mesafeyi tahmin et
                mesafe = self.traffic_light_detector.mesafe_tahmin_et(frame, koordinatlar)
                
                # Duruma göre aksiyon al
                if isik_durumu == "kirmizi":
                    if mesafe <= MIN_DURMA_MESAFESI:
                        self.motors.dur()
                        self.durum = "durma"
                        logger.info("Kırmızı ışık: Araç durduruluyor")
                        return False
                        
                elif isik_durumu == "sari":
                    if mesafe <= MIN_DURMA_MESAFESI:
                        self.motors.dur()
                        self.durum = "durma"
                        logger.info("Sarı ışık: Araç durduruluyor")
                        return False
                        
                elif isik_durumu == "yesil":
                    self.durum = "hareket"
                    logger.info("Yeşil ışık: Araç hareket ediyor")
                    return True
                
                self.son_trafik_isigi = isik_durumu
            
            return True
            
        except Exception as e:
            logger.error(f"Trafik ışığı kontrolü hatası: {str(e)}")
            self.motors.dur()
            return False
    
    def _yaya_gecidi_kontrolu(self, frame):
        """Yaya geçidi kontrolü yapar ve gerekli aksiyonu alır.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            bool: Devam edilip edilmeyeceği
        """
        try:
            # TODO: Yaya geçidi tespiti eklenecek
            # Şimdilik basit bir simülasyon
            if self.durum == "durma" and self.bekleme_baslangic is not None:
                gecen_sure = time.time() - self.bekleme_baslangic
                if gecen_sure >= YAYA_GECIDI_BEKLEME_SURESI:
                    self.durum = "hareket"
                    self.bekleme_baslangic = None
                    logger.info("Yaya geçidi bekleme süresi tamamlandı")
                    return True
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Yaya geçidi kontrolü hatası: {str(e)}")
            self.motors.dur()
            return False
    
    def _sollama_kontrolu(self, frame):
        """Sollama durumunu kontrol eder ve gerekli aksiyonu alır.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
        """
        try:
            # TODO: Sollama kontrolü eklenecek
            # Şimdilik basit bir simülasyon
            if self.durum == "sollama":
                # Sollama manevrasını tamamla
                self.durum = "hareket"
                logger.info("Sollama tamamlandı")
            
        except Exception as e:
            logger.error(f"Sollama kontrolü hatası: {str(e)}")
            self.motors.dur()
    
    def calistir(self):
        """Ana kontrol döngüsü."""
        try:
            while True:
                # Görüntü al
                frame = self.camera.capture_frame()
                if frame is None:
                    continue
                
                # Görüntüyü ön işle
                frame = self.camera.preprocess_frame(frame)
                
                # ROI uygula
                roi_frame, _ = self.camera.apply_roi(frame)
                
                # Şeritleri tespit et
                sol_serit, sag_serit, merkez_sapma = self.lane_detector.seritleri_bul(roi_frame)
                
                # Trafik ışığı kontrolü
                if not self._trafik_isigi_kontrolu(frame):
                    continue
                
                # Yaya geçidi kontrolü
                if not self._yaya_gecidi_kontrolu(frame):
                    continue
                
                # Sollama kontrolü
                self._sollama_kontrolu(frame)
                
                # Normal sürüş
                if self.durum == "hareket":
                    self._serit_takibi(merkez_sapma)
                
                time.sleep(0.05)  # CPU kullanımını azalt
                
        except KeyboardInterrupt:
            logger.info("Program kullanıcı tarafından sonlandırıldı")
        except Exception as e:
            logger.error(f"Ana döngüde hata: {str(e)}")
        finally:
            self.temizle()
    
    def temizle(self):
        """Tüm sistemleri temizler ve kapatır."""
        try:
            if hasattr(self, 'motors'):
                self.motors.temizle()
            if hasattr(self, 'camera'):
                self.camera.close()
            logger.info("Tüm sistemler kapatıldı")
        except Exception as e:
            logger.error(f"Temizleme sırasında hata: {str(e)}")

if __name__ == "__main__":
    # Log ayarlarını yapılandır
    logger.add("logs/otonom_arac.log", rotation="1 day")
    
    # Araç kontrolcüsünü başlat
    controller = VehicleController()
    controller.calistir() 