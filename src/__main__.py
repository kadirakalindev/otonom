"""
Otonom Araç Kontrol Sistemi - Ana Modül
"""
import sys
import signal
from loguru import logger
from src.control.vehicle_controller import VehicleController

def signal_handler(signum, frame):
    """Sinyal yakalayıcı."""
    logger.info("Program sonlandırılıyor...")
    sys.exit(0)

def main():
    """Ana program."""
    try:
        # Sinyal yakalayıcıyı ayarla
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Log ayarlarını yapılandır
        logger.add("logs/otonom_arac.log",
                  rotation="1 day",
                  format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
        
        # Başlangıç mesajı
        logger.info("Otonom araç kontrol sistemi başlatılıyor...")
        
        # Araç kontrolcüsünü başlat
        controller = VehicleController()
        controller.calistir()
        
    except Exception as e:
        logger.error(f"Program hatası: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 