"""
Motor Kontrol Modülü
"""
import time
from gpiozero import Motor, OutputDevice
from loguru import logger
from config.config import (
    MOTOR_SOL_ILERI, MOTOR_SOL_GERI,
    MOTOR_SAG_ILERI, MOTOR_SAG_GERI,
    MOTOR_SOL_PWM, MOTOR_SAG_PWM,
    MAX_PWM, MIN_PWM, BASLANGIC_HIZI
)

class MotorController:
    """gpiozero ile DC motorların kontrolü için sınıf."""
    
    def __init__(self):
        """Motor nesnelerini başlatır."""
        try:
            # Sol ve sağ motorları oluştur
            self.sol_motor = Motor(
                forward=MOTOR_SOL_ILERI,
                backward=MOTOR_SOL_GERI,
                enable=MOTOR_SOL_PWM
            )
            
            self.sag_motor = Motor(
                forward=MOTOR_SAG_ILERI,
                backward=MOTOR_SAG_GERI,
                enable=MOTOR_SAG_PWM
            )
            
            # Mevcut hız değerlerini sakla
            self.sol_hiz = 0
            self.sag_hiz = 0
            
            logger.info("Motor kontrol sistemi başlatıldı")
            
        except Exception as e:
            logger.error(f"Motor kontrol sistemi başlatılamadı: {str(e)}")
            self.temizle()
            raise
    
    def _hiz_sinirla(self, hiz):
        """PWM değerini sınırlar içinde tutar."""
        return max(MIN_PWM/100.0, min(MAX_PWM/100.0, abs(hiz)/100.0))
    
    def _yumusak_hizlanma(self, mevcut_hiz, hedef_hiz, adim=5, bekleme=0.05):
        """Motorları kademeli olarak hızlandırır/yavaşlatır."""
        if mevcut_hiz < hedef_hiz:
            return min(mevcut_hiz + adim, hedef_hiz)
        elif mevcut_hiz > hedef_hiz:
            return max(mevcut_hiz - adim, hedef_hiz)
        return mevcut_hiz
    
    def hiz_ayarla(self, sol_hiz, sag_hiz, yumusak=True):
        """Her iki motorun hızını ve yönünü ayarlar.
        
        Args:
            sol_hiz (int): Sol motor hızı (-100 ile 100 arası)
            sag_hiz (int): Sağ motor hızı (-100 ile 100 arası)
            yumusak (bool): Yumuşak hızlanma/yavaşlama kullanılsın mı
        """
        try:
            if yumusak:
                # Yumuşak hızlanma/yavaşlama
                while (self.sol_hiz != sol_hiz) or (self.sag_hiz != sag_hiz):
                    self.sol_hiz = self._yumusak_hizlanma(self.sol_hiz, sol_hiz)
                    self.sag_hiz = self._yumusak_hizlanma(self.sag_hiz, sag_hiz)
                    
                    # Sol motor kontrolü
                    if self.sol_hiz >= 0:
                        self.sol_motor.forward(self._hiz_sinirla(self.sol_hiz))
                    else:
                        self.sol_motor.backward(self._hiz_sinirla(self.sol_hiz))
                    
                    # Sağ motor kontrolü
                    if self.sag_hiz >= 0:
                        self.sag_motor.forward(self._hiz_sinirla(self.sag_hiz))
                    else:
                        self.sag_motor.backward(self._hiz_sinirla(self.sag_hiz))
                    
                    time.sleep(0.05)  # Yumuşak geçiş için bekleme
            else:
                # Direkt hız değişimi
                self.sol_hiz = sol_hiz
                self.sag_hiz = sag_hiz
                
                # Sol motor kontrolü
                if sol_hiz >= 0:
                    self.sol_motor.forward(self._hiz_sinirla(sol_hiz))
                else:
                    self.sol_motor.backward(self._hiz_sinirla(sol_hiz))
                
                # Sağ motor kontrolü
                if sag_hiz >= 0:
                    self.sag_motor.forward(self._hiz_sinirla(sag_hiz))
                else:
                    self.sag_motor.backward(self._hiz_sinirla(sag_hiz))
                    
        except Exception as e:
            logger.error(f"Hız ayarlama hatası: {str(e)}")
            self.dur()
    
    def ileri(self, hiz=BASLANGIC_HIZI):
        """Aracı ileri yönde hareket ettirir."""
        self.hiz_ayarla(hiz, hiz)
        logger.debug(f"İleri hareket: Hız={hiz}")
    
    def geri(self, hiz=BASLANGIC_HIZI):
        """Aracı geri yönde hareket ettirir."""
        self.hiz_ayarla(-hiz, -hiz)
        logger.debug(f"Geri hareket: Hız={hiz}")
    
    def sola_don(self, hiz=BASLANGIC_HIZI):
        """Aracı sola döndürür."""
        self.hiz_ayarla(-hiz, hiz)
        logger.debug(f"Sola dönüş: Hız={hiz}")
    
    def saga_don(self, hiz=BASLANGIC_HIZI):
        """Aracı sağa döndürür."""
        self.hiz_ayarla(hiz, -hiz)
        logger.debug(f"Sağa dönüş: Hız={hiz}")
    
    def dur(self):
        """Tüm motorları durdurur."""
        try:
            self.sol_motor.stop()
            self.sag_motor.stop()
            self.sol_hiz = 0
            self.sag_hiz = 0
            logger.debug("Araç durduruldu")
        except Exception as e:
            logger.error(f"Durdurma hatası: {str(e)}")
    
    def temizle(self):
        """Motor nesnelerini temizler."""
        try:
            self.dur()
            self.sol_motor.close()
            self.sag_motor.close()
            logger.info("Motor kontrol sistemi kapatıldı")
        except Exception as e:
            logger.error(f"Temizleme hatası: {str(e)}") 