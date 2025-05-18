"""
Şerit Algılama Modülü
"""
import cv2
import numpy as np
from loguru import logger
from config.config import (
    SERIT_HSV_ALT,
    SERIT_HSV_UST,
    SERIT_GENISLIK
)

class LaneDetector:
    """Şerit algılama ve takibi için sınıf."""
    
    def __init__(self):
        """Şerit algılama parametrelerini başlatır."""
        # Şerit algılama için eşik değerleri
        self.hsv_alt = np.array(SERIT_HSV_ALT)
        self.hsv_ust = np.array(SERIT_HSV_UST)
        
        # Şerit bilgileri
        self.son_sol_serit = None
        self.son_sag_serit = None
        self.serit_genislik = SERIT_GENISLIK
        
        # Perspektif dönüşümü için matrisler
        self.perspektif_matrix = None
        self.ters_perspektif_matrix = None
        
        # Kalibrasyon durumu
        self.kalibre_edildi = False
        
        logger.info("Şerit algılama sistemi başlatıldı")
    
    def _serit_maske_olustur(self, frame):
        """Beyaz şeritleri algılamak için HSV maskesi oluşturur.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            numpy.ndarray: İkili maske görüntüsü
        """
        try:
            # BGR'den HSV'ye dönüşüm
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Beyaz renk maskesi
            mask = cv2.inRange(hsv, self.hsv_alt, self.hsv_ust)
            
            # Morfolojik işlemler
            kernel = np.ones((5,5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            return mask
            
        except Exception as e:
            logger.error(f"Maske oluşturma hatası: {str(e)}")
            return None
    
    def _serit_noktalari_bul(self, mask):
        """Maskedeki şerit noktalarını bulur.
        
        Args:
            mask (numpy.ndarray): İkili maske görüntüsü
            
        Returns:
            tuple: (sol_noktalar, sag_noktalar) - Şerit noktaları listeleri
        """
        try:
            # Görüntüyü dikey olarak böl
            height, width = mask.shape
            sol_bolge = mask[:, :width//2]
            sag_bolge = mask[:, width//2:]
            
            # Her satır için şerit noktalarını bul
            sol_noktalar = []
            sag_noktalar = []
            
            for y in range(height):
                # Sol şerit için noktalar
                sol_satir = sol_bolge[y, :]
                sol_beyaz = np.where(sol_satir == 255)[0]
                if len(sol_beyaz) > 0:
                    sol_x = int(np.mean(sol_beyaz))
                    sol_noktalar.append((sol_x, y))
                
                # Sağ şerit için noktalar
                sag_satir = sag_bolge[y, :]
                sag_beyaz = np.where(sag_satir == 255)[0]
                if len(sag_beyaz) > 0:
                    sag_x = int(np.mean(sag_beyaz)) + width//2
                    sag_noktalar.append((sag_x, y))
            
            return sol_noktalar, sag_noktalar
            
        except Exception as e:
            logger.error(f"Şerit noktaları bulma hatası: {str(e)}")
            return [], []
    
    def _serit_egrisini_hesapla(self, noktalar, frame_shape):
        """Şerit noktalarına en uygun eğriyi hesaplar.
        
        Args:
            noktalar (list): (x,y) koordinat çiftleri
            frame_shape (tuple): Görüntü boyutları
            
        Returns:
            numpy.ndarray: Eğri katsayıları
        """
        if len(noktalar) < 2:
            return None
            
        try:
            # Noktaları x ve y dizilerine ayır
            x = np.array([p[0] for p in noktalar])
            y = np.array([p[1] for p in noktalar])
            
            # İkinci dereceden polinom uydur
            katsayilar = np.polyfit(y, x, 2)
            
            return katsayilar
            
        except Exception as e:
            logger.error(f"Eğri hesaplama hatası: {str(e)}")
            return None
    
    def seritleri_bul(self, frame):
        """Görüntüdeki şeritleri tespit eder.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            tuple: (sol_serit, sag_serit, merkez_sapma) - Şerit eğrileri ve merkez sapması
        """
        if frame is None:
            return None, None, 0
            
        try:
            # Şerit maskesi oluştur
            mask = self._serit_maske_olustur(frame)
            if mask is None:
                return self.son_sol_serit, self.son_sag_serit, 0
            
            # Şerit noktalarını bul
            sol_noktalar, sag_noktalar = self._serit_noktalari_bul(mask)
            
            # Eğrileri hesapla
            sol_serit = self._serit_egrisini_hesapla(sol_noktalar, frame.shape)
            sag_serit = self._serit_egrisini_hesapla(sag_noktalar, frame.shape)
            
            # Geçerli şeritleri güncelle
            if sol_serit is not None:
                self.son_sol_serit = sol_serit
            if sag_serit is not None:
                self.son_sag_serit = sag_serit
            
            # Merkez sapmasını hesapla
            merkez_sapma = self._merkez_sapmasini_hesapla(frame.shape[1])
            
            return self.son_sol_serit, self.son_sag_serit, merkez_sapma
            
        except Exception as e:
            logger.error(f"Şerit bulma hatası: {str(e)}")
            return self.son_sol_serit, self.son_sag_serit, 0
    
    def _merkez_sapmasini_hesapla(self, frame_width):
        """Aracın şerit merkezinden sapmasını hesaplar.
        
        Args:
            frame_width (int): Görüntü genişliği
            
        Returns:
            float: Merkez sapması (piksel)
        """
        try:
            if self.son_sol_serit is None or self.son_sag_serit is None:
                return 0
            
            # Görüntünün alt kısmında şerit pozisyonlarını hesapla
            y = frame_width - 1
            sol_x = np.polyval(self.son_sol_serit, y)
            sag_x = np.polyval(self.son_sag_serit, y)
            
            # Şerit merkezi
            serit_merkezi = (sol_x + sag_x) / 2
            
            # Görüntü merkezi
            goruntu_merkezi = frame_width / 2
            
            # Sapma miktarı (pozitif değer sağa sapma)
            return serit_merkezi - goruntu_merkezi
            
        except Exception as e:
            logger.error(f"Merkez sapması hesaplama hatası: {str(e)}")
            return 0
    
    def serit_tipi_kontrol(self, frame):
        """Şeridin kesikli mi yoksa düz mü olduğunu kontrol eder.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            str: 'kesikli' veya 'duz'
        """
        try:
            # Şerit maskesi oluştur
            mask = self._serit_maske_olustur(frame)
            if mask is None:
                return 'duz'  # Varsayılan olarak düz kabul et
            
            # Dikey projeksiyon profili
            dikey_profil = np.sum(mask, axis=1)
            
            # Profildeki sıfır geçişlerini say
            sifir_gecisleri = len(np.where(np.diff(dikey_profil > 0))[0])
            
            # Eşik değeri (deneysel olarak ayarlanmalı)
            esik = 10
            
            return 'kesikli' if sifir_gecisleri > esik else 'duz'
            
        except Exception as e:
            logger.error(f"Şerit tipi kontrol hatası: {str(e)}")
            return 'duz'  # Hata durumunda güvenli seçenek 
    
    def perspektif_kalibrasyonu(self, frame):
        """Kamera perspektif dönüşümü için kalibrasyon yapar.
        
        Args:
            frame (numpy.ndarray): Kalibrasyon için kullanılacak görüntü
            
        Returns:
            bool: Kalibrasyon başarılı mı
        """
        try:
            height, width = frame.shape[:2]
            
            # Kaynak noktaları (pistteki dörtgen)
            # Bu değerler deneysel olarak ayarlanmalı
            src_points = np.float32([
                [width * 0.1, height * 0.8],  # Sol alt
                [width * 0.4, height * 0.5],  # Sol üst
                [width * 0.6, height * 0.5],  # Sağ üst
                [width * 0.9, height * 0.8]   # Sağ alt
            ])
            
            # Hedef noktaları (kuş bakışı görünüm)
            dst_points = np.float32([
                [width * 0.2, height],        # Sol alt
                [width * 0.2, 0],             # Sol üst
                [width * 0.8, 0],             # Sağ üst
                [width * 0.8, height]         # Sağ alt
            ])
            
            # Perspektif dönüşüm matrislerini hesapla
            self.perspektif_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            self.ters_perspektif_matrix = cv2.getPerspectiveTransform(dst_points, src_points)
            
            self.kalibre_edildi = True
            logger.info("Perspektif kalibrasyonu tamamlandı")
            return True
            
        except Exception as e:
            logger.error(f"Perspektif kalibrasyonu hatası: {str(e)}")
            return False
    
    def perspektif_donusumu_uygula(self, frame):
        """Görüntüye perspektif dönüşümü uygular.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            numpy.ndarray: Kuş bakışı görünüm
        """
        if not self.kalibre_edildi:
            logger.warning("Perspektif kalibrasyonu yapılmamış!")
            return frame
            
        try:
            height, width = frame.shape[:2]
            return cv2.warpPerspective(frame, self.perspektif_matrix, (width, height))
            
        except Exception as e:
            logger.error(f"Perspektif dönüşümü hatası: {str(e)}")
            return frame
    
    def kalibrasyon_goruntusunu_goster(self, frame):
        """Kalibrasyon için referans noktaları ile görüntüyü gösterir.
        
        Args:
            frame (numpy.ndarray): Gösterilecek görüntü
        """
        try:
            height, width = frame.shape[:2]
            
            # Referans noktaları
            points = np.float32([
                [width * 0.1, height * 0.8],  # Sol alt
                [width * 0.4, height * 0.5],  # Sol üst
                [width * 0.6, height * 0.5],  # Sağ üst
                [width * 0.9, height * 0.8]   # Sağ alt
            ])
            
            # Noktaları görüntü üzerine çiz
            kalibrasyon_goruntusu = frame.copy()
            for i in range(4):
                cv2.circle(kalibrasyon_goruntusu, 
                          (int(points[i][0]), int(points[i][1])), 
                          5, (0, 0, 255), -1)
            
            # Noktaları birleştiren çizgileri çiz
            cv2.polylines(kalibrasyon_goruntusu, 
                         [points.astype(np.int32)], 
                         True, (0, 255, 0), 2)
            
            return kalibrasyon_goruntusu
            
        except Exception as e:
            logger.error(f"Kalibrasyon görüntüsü oluşturma hatası: {str(e)}")
            return frame 