import RPi.GPIO as GPIO
import time
import os

# Konfigurasi pin GPIO
BUTTON_PIN = 16  # Ganti dengan pin GPIO yang Anda gunakan
HOLD_TIME = 3    # Waktu tahan tombol dalam detik

# Konfigurasi mode GPIO (BCM atau BOARD)
GPIO.setmode(GPIO.BCM)

# Atur pin tombol sebagai input dengan pull-up internal
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print(f"Skrip shutdown aktif. Tahan tombol selama {HOLD_TIME} detik untuk mematikan Raspberry Pi.")

# Variabel untuk melacak waktu penekanan tombol
button_press_time = None

def button_event_handler(channel):
    global button_press_time

    if GPIO.input(BUTTON_PIN) == GPIO.LOW:  # Tombol Ditekan (LOW karena pull-up)
        # Jika ini penekanan baru atau tombol belum dilepas
        if button_press_time is None:
            button_press_time = time.time()
            print(f"Tombol ditekan. Tahan selama {HOLD_TIME} detik...")
    else:  # Tombol Dilepas (HIGH)
        # Reset jika tombol dilepas sebelum waktu tahan terpenuhi
        if button_press_time is not None:
            elapsed_time = time.time() - button_press_time
            if elapsed_time < HOLD_TIME:
                print(f"Tombol dilepas terlalu cepat ({elapsed_time:.2f} detik). Shutdown dibatalkan.")
            button_press_time = None # Reset waktu penekanan

# Tambahkan event deteksi tombol untuk kedua tepi (rising dan falling)
# Ini memungkinkan kita untuk melacak kapan tombol ditekan dan dilepas
GPIO.add_event_detect(BUTTON_PIN, GPIO.BOTH, callback=button_event_handler, bouncetime=50)

try:
    while True:
        # Periksa setiap detik apakah tombol masih ditekan dan sudah melewati waktu tahan
        if button_press_time is not None:
            elapsed_time = time.time() - button_press_time
            if elapsed_time >= HOLD_TIME:
                print(f"Tombol ditahan selama {elapsed_time:.2f} detik. Mematikan Raspberry Pi sekarang...")
                os.system("sudo shutdown -h now")
                # Skrip akan berakhir di sini karena Pi akan mati
                break # Keluar dari loop

        time.sleep(0.1) # Cek lebih sering untuk deteksi tahan tombol yang lebih responsif

except KeyboardInterrupt:
    print("\nSkrip dihentikan.")
finally:
    GPIO.cleanup() # Bersihkan semua pengaturan GPIO sebelum keluar
    print("GPIO dibersihkan.")
