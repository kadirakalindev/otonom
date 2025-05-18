"""
Kamera Kalibrasyon Aracı
"""
import cv2
import numpy as np
from loguru import logger
import time
from src.camera.camera_controller import CameraController
from src.detection.lane_detector import LaneDetector

def main():
    """Kalibrasyon aracı ana fonksiyonu."""
    try:
        # Kamera ve şerit detektörünü başlat
        camera = CameraController()
        lane_detector = LaneDetector()
        
        # Pencere oluştur ve boyutlandır
        cv2.namedWindow('Kalibrasyon', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Kalibrasyon', 640, 480)
        cv2.namedWindow('Kuş Bakışı Görünüm', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Kuş Bakışı Görünüm', 640, 480)
        
        # FPS kontrolü için değişkenler
        fps_limit = 30  # Maksimum FPS
        frame_delay = 1.0 / fps_limit
        last_frame_time = time.time()
        
        while True:
            # FPS kontrolü
            current_time = time.time()
            elapsed = current_time - last_frame_time
            if elapsed < frame_delay:
                continue
            
            last_frame_time = current_time
            
            # Görüntü al
            frame = camera.capture_frame()
            if frame is None:
                time.sleep(0.1)  # Kamera hazır değilse biraz bekle
                continue
            
            try:
                # Görüntüyü yeniden boyutlandır (performans için)
                frame = cv2.resize(frame, (640, 480))
                
                # Görüntüyü ön işle
                frame = camera.preprocess_frame(frame)
                
                # ROI uygula
                roi_frame, _ = camera.apply_roi(frame)
                
                # Kalibrasyon görüntüsünü göster
                kalibrasyon_goruntusu = lane_detector.kalibrasyon_goruntusunu_goster(roi_frame)
                cv2.imshow('Kalibrasyon', kalibrasyon_goruntusu)
                
                # Perspektif dönüşümü uygula
                if not lane_detector.kalibre_edildi:
                    lane_detector.perspektif_kalibrasyonu(roi_frame)
                
                kus_bakisi = lane_detector.perspektif_donusumu_uygula(roi_frame)
                cv2.imshow('Kuş Bakışı Görünüm', kus_bakisi)
                
            except Exception as e:
                logger.error(f"Görüntü işleme hatası: {str(e)}")
                continue
            
            # Tuş kontrolü - Non-blocking wait
            key = cv2.waitKey(1) & 0xFF
            
            # 'q' tuşu ile çık
            if key == ord('q'):
                break
            # 'c' tuşu ile yeniden kalibre et
            elif key == ord('c'):
                lane_detector.kalibre_edildi = False
            # 's' tuşu ile kaydet
            elif key == ord('s'):
                try:
                    timestamp = time.strftime("%Y%m%d-%H%M%S")
                    cv2.imwrite(f'kalibrasyon_{timestamp}.jpg', kalibrasyon_goruntusu)
                    cv2.imwrite(f'kus_bakisi_{timestamp}.jpg', kus_bakisi)
                    logger.info("Görüntüler kaydedildi")
                except Exception as e:
                    logger.error(f"Görüntü kaydetme hatası: {str(e)}")
            
            # CPU kullanımını azaltmak için kısa bekleme
            time.sleep(0.01)
        
    except Exception as e:
        logger.error(f"Kalibrasyon aracı hatası: {str(e)}")
    finally:
        # Temizlik işlemleri
        cv2.destroyAllWindows()
        camera.close()
        logger.info("Kalibrasyon aracı kapatıldı")

if __name__ == "__main__":
    # Log ayarlarını yapılandır
    logger.add("logs/kalibrasyon.log",
               rotation="1 day",
               format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
               enqueue=True)  # Thread-safe logging
    
    main() 