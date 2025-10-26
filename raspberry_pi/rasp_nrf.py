#!/usr/bin/env python3
"""
rasp_nrf.py - Modul Gabungan untuk Raspberry Pi

Fungsi:
1. Bertindak sebagai pelayan web (server) Flask untuk menerima arahan dari Mini PC.
2. Menghantar isyarat melalui modul NRF24L01 kepada Arduino.

CARA GUNA:
Jalankan skrip ini secara terus pada Raspberry Pi:
$ python3 rasp_nrf.py

Ia akan memulakan pelayan yang menunggu arahan dari Mini PC pada
http://<Alamat IP Raspberry Pi Anda>:5000/trigger-relay
"""

# Import pustaka yang diperlukan
from RF24 import RF24, RF24_PA_LOW, RF24_250KBPS
from flask import Flask, jsonify, request
import time
import socket
import logging # Untuk logging yang lebih baik

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# =============================================================
# BAHAGIAN 1: KONFIGURASI UMUM
# =============================================================
class Config:
    # NRF24L01 Configuration
    CE_PIN = 22             # BCM pin 22 (GPIO22)
    CSN_PIN = 0             # CE0 pada SPI bus 0 (BCM pin 8)
    PIPE_ADDRESS = b"SIGNL" # Alamat paip komunikasi NRF. Mesti sama dengan Arduino!
    PA_LEVEL = RF24_PA_LOW  # Kuasa output: RF24_PA_MIN, RF24_PA_LOW, RF24_PA_HIGH, RF24_PA_MAX
    DATA_RATE = RF24_250KBPS # Kadar data: RF24_250KBPS, RF24_1MBPS, RF24_2MBPS
    CHANNEL = 76            # Saluran komunikasi (0-125). Mesti sama dengan Arduino.
    NRF_RETRIES = 5         # Bilangan percubaan penghantaran NRF
    NRF_RETRY_DELAY = 0.1   # Kelewatan antara percubaan (saat)

    # Flask Server Configuration
    FLASK_HOST = '0.0.0.0'  # Host untuk pelayan Flask (0.0.0.0 = boleh diakses dari mana-mana IP)
    FLASK_PORT = 5000       # Port untuk pelayan Flask
    FLASK_DEBUG = False     # Mod debug Flask (False untuk pengeluaran)

# =============================================================
# BAHAGIAN 2: LOGIK UNTUK KOMUNIKASI NRF24L01
# =============================================================

class NRF24L01Handler:
    def __init__(self):
        self.radio = RF24(Config.CE_PIN, Config.CSN_PIN)
        self.is_initialized = False

    def setup_radio(self) -> bool:
        """
        Mengkonfigurasi modul NRF24L01. Dipanggil sekali atau jika radio belum diinisialisasi.
        """
        if self.is_initialized:
            return True

        logger.info("Memulakan NRF24L01...")
        try:
            if not self.radio.begin():
                logger.critical("Modul NRF24L01 tidak dikesan! Periksa pendawaian.")
                return False

            self.radio.setPALevel(Config.PA_LEVEL)
            self.radio.setDataRate(Config.DATA_RATE)
            self.radio.setChannel(Config.CHANNEL)
            self.radio.openWritingPipe(Config.PIPE_ADDRESS)
            self.radio.stopListening()

            self.is_initialized = True
            logger.info("Radio NRF24L01 sedia untuk menghantar.")
            return True
        except Exception as e:
            logger.critical(f"Ralat semasa memulakan NRF24L01: {e}")
            return False

    def send_signal(self, message: str) -> bool:
        """
        Menghantar mesej melalui NRF24L01 kepada peranti penerima (Arduino).
        Cuba beberapa kali jika penghantaran gagal (tiada ACK diterima).
        """
        if not self.is_initialized and not self.setup_radio():
            logger.error("Gagal menyediakan radio NRF untuk penghantaran.")
            return False

        encoded_message = message.encode('utf-8')
        for attempt in range(1, Config.NRF_RETRIES + 1):
            logger.info(f" (Percubaan {attempt}/{Config.NRF_RETRIES}) Menghantar: '{message}'...")
            if self.radio.write(encoded_message):
                logger.info(f"Berjaya! Arduino telah menerima isyarat '{message}'.")
                return True
            else:
                logger.warning("Gagal! Tiada ACK diterima dari Arduino.")
                time.sleep(Config.NRF_RETRY_DELAY)

        logger.error(f"Gagal menghantar isyarat selepas {Config.NRF_RETRIES} percubaan.")
        return False

# =============================================================
# BAHAGIAN 3: LOGIK PELAYAN WEB (FLASK) UNTUK MENERIMA ARAHAN
# =============================================================

app = Flask(__name__)
nrf_handler = NRF24L01Handler() # Inisialisasi NRF handler

# Fungsi untuk mendapatkan alamat IP tempatan Raspberry Pi
def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80)) # Tidak perlu sambungan sebenar, hanya untuk mendapatkan IP
        IP = s.getsockname()[0]
    except Exception:
        IP = "127.0.0.1" # Fallback jika tiada sambungan
    finally:
        s.close()
    return IP

@app.route('/trigger-relay', methods=['GET', 'POST'])
def trigger_relay_endpoint():
    """
    Endpoint dipanggil oleh Mini PC untuk kawal relay.
    GET  -> aktifkan relay (RELAY_ON)
    POST -> hantar data JSON {"action": "RELAY_OFF"} contohnya
    """
    message_to_send = "RELAY_ON"  # Default kalau GET

    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data and 'action' in data:
            message_to_send = data['action']  # boleh RELAY_ON / RELAY_OFF
            logger.info(f"Arahan POST diterima: {message_to_send}")
        else:
            logger.info("POST tanpa data, fallback ke RELAY_ON")
    else:
        logger.info("GET diterima, hantar RELAY_ON")

    success = nrf_handler.send_signal(message_to_send)

    if success:
        return jsonify({"status": "success", "message": f"NRF signal '{message_to_send}' sent."}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send NRF signal."}), 500
        
# =============================================================
# BAHAGIAN 4: BLOK UTAMA UNTUK MENJALANKAN PELAYAN
# =============================================================

if __name__ == "__main__":
    raspi_ip = get_ip_address()
    
    logger.info("="*50)
    logger.info("Memulakan Pelayan NRF pada Raspberry Pi")
    logger.info("="*50)
    logger.info("Menunggu arahan dari Mini PC pada:")
    logger.info(f"http://{raspi_ip}:{Config.FLASK_PORT}/trigger-relay")
    logger.info("Pastikan Mini PC menghantar permintaan ke alamat IP ini.")
    logger.info("Tekan Ctrl+C untuk berhenti.")

    try:
        # Inisialisasi radio NRF di awal
        if not nrf_handler.setup_radio():
            logger.critical("NRF24L01 tidak dapat dimulakan. Program akan berjalan, tetapi fungsi NRF tidak aktif.")

        app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
    except KeyboardInterrupt:
        logger.info("Program dihentikan oleh pengguna (Ctrl+C).")
    except Exception as e:
        logger.critical(f"Ralat kritikal semasa menjalankan pelayan Flask: {e}", exc_info=True)
