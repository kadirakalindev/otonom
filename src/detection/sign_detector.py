"""
Trafik Tabelası Algılama Modülü - Şekil Tabanlı Tespit
"""
import cv2
import numpy as np
from loguru import logger
import time

class SignDetector:
    """Şekil tabanlı trafik tabelası algılama sınıfı."""
    
    def __init__(self, kamera_cozunurluk=(640, 480), min_alan_oran=0.01, max_alan_oran=0.1):
        """
        Tabela algılama sistemini başlatır.
        
        Args:
            kamera_cozunurluk (tuple): Kamera çözünürlüğü (genişlik, yükseklik)
            min_alan_oran (float): Minimum şekil alanı oranı (görüntü alanına göre)
            max_alan_oran (float): Maximum şekil alanı oranı (görüntü alanına göre)
        """
        # Kamera çözünürlüğü
        self.genislik, self.yukseklik = kamera_cozunurluk
        goruntu_alani = self.genislik * self.yukseklik
        
        # Şekil alanı sınırları (görüntü boyutuna göre dinamik)
        self.min_alan = int(goruntu_alani * min_alan_oran)
        self.max_alan = int(goruntu_alani * max_alan_oran)
        
        # Görüntü işleme parametreleri
        self.blur_kernel = (5, 5)
        self.canny_alt = 50
        self.canny_ust = 150
        self.dilate_kernel = np.ones((5,5), np.uint8)
        self.dilate_iter = 1
        
        # Şekil tespit parametreleri
        self.epsilon_oran = 0.04
        self.kare_oran_alt = 0.8
        self.kare_oran_ust = 1.2
        self.dairesellik_esik = 0.8
        
        # Tabela bilgileri (cm)
        self.direk_yukseklik = 20
        self.tabela_yukseklik = 13
        self.toplam_yukseklik = self.direk_yukseklik + self.tabela_yukseklik
        
        # FPS hesaplama için değişkenler
        self.fps = 0
        self.fps_sayac = 0
        self.son_fps_guncelleme = time.time()
        self.fps_guncelleme_suresi = 1.0  # saniye
        
        # Tabela tipleri ve renk kodları
        self.TABELA_TIPI = {
            "dortgen": "park",
            "ucgen": "hemzemin_gecit",
            "daire": "sollama_serbest"
        }
        
        self.TABELA_RENK = {
            "park": (0, 255, 0),        # Yeşil
            "hemzemin_gecit": (0, 0, 255),  # Kırmızı
            "sollama_serbest": (255, 0, 0)  # Mavi
        }
        
        logger.info(f"Şekil tabanlı tabela algılama sistemi başlatıldı - Min Alan: {self.min_alan}, Max Alan: {self.max_alan}")
    
    def parametreleri_ayarla(self, blur_kernel=(5,5), canny_alt=50, canny_ust=150,
                            epsilon_oran=0.04, dairesellik_esik=0.8):
        """Görüntü işleme parametrelerini ayarlar."""
        if not isinstance(blur_kernel, tuple) or len(blur_kernel) != 2:
            raise ValueError("blur_kernel 2 elemanlı tuple olmalı")
            
        if not 0 <= canny_alt <= canny_ust <= 255:
            raise ValueError("Canny eşik değerleri 0-255 arasında olmalı")
            
        if not 0 < epsilon_oran < 1:
            raise ValueError("epsilon_oran 0-1 arasında olmalı")
            
        if not 0 < dairesellik_esik < 1:
            raise ValueError("dairesellik_esik 0-1 arasında olmalı")
        
        self.blur_kernel = blur_kernel
        self.canny_alt = canny_alt
        self.canny_ust = canny_ust
        self.epsilon_oran = epsilon_oran
        self.dairesellik_esik = dairesellik_esik
        
        logger.info("Görüntü işleme parametreleri güncellendi")
    
    def _fps_guncelle(self):
        """FPS değerini günceller."""
        self.fps_sayac += 1
        gecen_sure = time.time() - self.son_fps_guncelleme
        
        if gecen_sure >= self.fps_guncelleme_suresi:
            self.fps = self.fps_sayac / gecen_sure
            self.fps_sayac = 0
            self.son_fps_guncelleme = time.time()
    
    def _sekil_tespit(self, kontur):
        """Konturun şeklini tespit eder.
        
        Args:
            kontur: Şekil konturu
            
        Returns:
            str: Şekil tipi ('dortgen', 'ucgen', 'daire' veya None)
        """
        try:
            # Yaklaşık çokgen oluştur
            cevre = cv2.arcLength(kontur, True)
            if cevre == 0:
                return None
                
            epsilon = self.epsilon_oran * cevre
            approx = cv2.approxPolyDP(kontur, epsilon, True)
            
            # Köşe sayısına göre şekli belirle
            koseler = len(approx)
            
            # Dairesellik oranı
            alan = cv2.contourArea(kontur)
            dairesellik = 4 * np.pi * alan / (cevre * cevre)
            
            if koseler == 3:
                return 'ucgen'
            elif koseler == 4:
                # Kare/dikdörtgen kontrolü
                x, y, w, h = cv2.boundingRect(approx)
                if w == 0 or h == 0:
                    return None
                    
                aspect_ratio = float(w)/h
                if self.kare_oran_alt <= aspect_ratio <= self.kare_oran_ust:
                    return 'dortgen'
            elif koseler > 4 and dairesellik > self.dairesellik_esik:
                return 'daire'
            
            return None
            
        except Exception as e:
            logger.error(f"Şekil tespit hatası: {str(e)}")
            return None
    
    def _goruntu_on_isle(self, frame):
        """Görüntüyü işlemeye hazırlar.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            numpy.ndarray: İşlenmiş görüntü
        """
        if frame is None or frame.size == 0:
            raise ValueError("Geçersiz görüntü")
            
        try:
            # Gri tonlamaya çevir
            gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Gürültü azaltma
            blur = cv2.GaussianBlur(gri, self.blur_kernel, 0)
            
            # Kenar tespiti
            kenarlar = cv2.Canny(blur, self.canny_alt, self.canny_ust)
            
            # Morfolojik işlemler
            kenarlar = cv2.dilate(kenarlar, self.dilate_kernel, 
                                iterations=self.dilate_iter)
            
            return kenarlar
            
        except Exception as e:
            logger.error(f"Görüntü ön işleme hatası: {str(e)}")
            return None
    
    def tabelalari_tespit_et(self, frame):
        """
        Görüntüdeki trafik tabelalarını tespit eder.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            
        Returns:
            list: [(tabela_tipi, alan, bbox), ...] formatında tespit listesi
        """
        if frame is None or frame.size == 0:
            logger.error("Geçersiz görüntü")
            return []
            
        try:
            # FPS güncelle
            self._fps_guncelle()
            
            # Görüntüyü ön işle
            islenmiş = self._goruntu_on_isle(frame)
            if islenmiş is None:
                return []
            
            # Konturları bul
            konturlar, _ = cv2.findContours(islenmiş, cv2.RETR_EXTERNAL, 
                                          cv2.CHAIN_APPROX_SIMPLE)
            
            tespitler = []
            for kontur in konturlar:
                # Alan kontrolü
                alan = cv2.contourArea(kontur)
                if self.min_alan <= alan <= self.max_alan:
                    # Şekil tespiti
                    sekil = self._sekil_tespit(kontur)
                    if sekil:
                        # Sınırlayıcı kutu
                        x, y, w, h = cv2.boundingRect(kontur)
                        
                        # Tabela tipini belirle
                        tabela_tipi = self.TABELA_TIPI.get(sekil)
                        if tabela_tipi:
                            tespitler.append((tabela_tipi, alan, (x, y, w, h)))
            
            return tespitler
            
        except Exception as e:
            logger.error(f"Tabela tespit hatası: {str(e)}")
            return []
    
    def goruntu_isle(self, frame, tespitleri_ciz=True):
        """
        Görüntüyü işler ve opsiyonel olarak tespitleri çizer.
        
        Args:
            frame (numpy.ndarray): İşlenecek görüntü
            tespitleri_ciz (bool): Tespitler görüntü üzerine çizilsin mi
            
        Returns:
            tuple: (işlenmiş_görüntü, tespitler)
        """
        if frame is None or frame.size == 0:
            logger.error("Geçersiz görüntü")
            return None, []
            
        try:
            # Görüntü boyutlarını kontrol et
            h, w = frame.shape[:2]
            if (w, h) != (self.genislik, self.yukseklik):
                frame = cv2.resize(frame, (self.genislik, self.yukseklik))
            
            # Tespitleri al
            tespitler = self.tabelalari_tespit_et(frame)
            
            if tespitleri_ciz:
                # Tespitleri görüntü üzerine çiz
                for tabela_tipi, alan, (x, y, w, h) in tespitler:
                    renk = self.TABELA_RENK.get(tabela_tipi, (0, 255, 0))
                    
                    # Çerçeve çiz
                    cv2.rectangle(frame, (x, y), (x+w, y+h), renk, 2)
                    
                    # Etiket metni
                    etiket = f"{tabela_tipi}"
                    
                    # Etiket arka planı
                    (tw, th), _ = cv2.getTextSize(etiket, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    cv2.rectangle(frame, (x, y-20), (x+tw, y), renk, -1)
                    
                    # Etiketi yaz
                    cv2.putText(frame, etiket, (x, y-5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # FPS göster
                cv2.putText(frame, f"FPS: {self.fps:.1f}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                           1, (0, 255, 0), 2)
            
            return frame, tespitler
            
        except Exception as e:
            logger.error(f"Görüntü işleme hatası: {str(e)}")
            return frame, [] 