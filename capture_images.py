import cv2
import os
import re
import sys

# ==================== KONFIGURASI ====================
STREAM_URL = "http://192.168.10.1:8000/video"
DATASET_PATH = "dataset"
IMAGES_TO_CAPTURE = 30
HAAR_CASCADE_PATH = 'haarcascade_frontalface_default.xml'
# =====================================================

def capture_student_images(student_name):
    # Bersihkan nama untuk folder
    safe_folder_name = re.sub(r'[\s\W]+', '_', student_name)
    student_path = os.path.join(DATASET_PATH, safe_folder_name)
    os.makedirs(student_path, exist_ok=True)
    print(f"✅ Folder untuk '{student_name}' telah disediakan di '{student_path}'")

    if not os.path.exists(HAAR_CASCADE_PATH):
        print(f"❌ Ralat: Fail '{HAAR_CASCADE_PATH}' tidak dijumpai.")
        return
    face_detector = cv2.CascadeClassifier(HAAR_CASCADE_PATH)

    print(f"🔄 Cuba menyambung ke stream video di {STREAM_URL}...")
    video_capture = cv2.VideoCapture(STREAM_URL)

    if not video_capture.isOpened():
        print("❌ Gagal menyambung ke stream video.")
        return

    print("✅ Sambungan berjaya. Memulakan tangkapan gambar...")
    print("Tekan 's' untuk mula. Tekan 'q' untuk keluar.")

    img_count = 0
    capture_started = False

    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("⚠️ Gagal membaca frame.")
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            if capture_started:
                img_count += 1
                face_image_path = os.path.join(student_path, f"{img_count}.jpg")
                cv2.imwrite(face_image_path, gray_frame[y:y+h, x:x+w])
                print(f"✔️ Gambar ke-{img_count} berjaya disimpan!")

        status_text = f"Simpan: {img_count}/{IMAGES_TO_CAPTURE}" if capture_started else "Tekan 's' untuk mula"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow('Tangkapan Gambar Pelajar', frame)

        if img_count >= IMAGES_TO_CAPTURE:
            print(f"\n✅ {IMAGES_TO_CAPTURE} gambar telah berjaya ditangkap.")
            break

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("⏹️ Proses dihentikan.")
            break
        elif key == ord('s') and not capture_started:
            print("🚀 Memulakan proses tangkapan gambar...")
            capture_started = True

    video_capture.release()
    cv2.destroyAllWindows()
    print("Sila jalankan 'enroll_student.py' untuk daftar wajah.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("❌ Sila masukkan nama pelajar sebagai argumen!")
        sys.exit(1)

    student_name = sys.argv[1]
    print(f"Nama pelajar: {student_name}")
    capture_student_images(student_name)

