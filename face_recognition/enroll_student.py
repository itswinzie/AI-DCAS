# enroll_student.py (Versi Diperbaiki untuk Command-Line)
import sqlite3
import face_recognition
import os
import numpy as np
import re
import sys # <-- PENTING: Import sys untuk akses argumen & exit

DB_NAME = "attendance_system.db"
DATASET_BASE_DIR = "dataset"
ENCODINGS_DIR = "encodings"

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        # Apabila skrip dijalankan dari command-line, kita mahu ralat dipaparkan di stderr
        print(f"DB Error: {e}", file=sys.stderr)
    return conn

def get_representative_encoding(image_paths):
    all_encodings = []
    for image_path in image_paths:
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                all_encodings.append(encodings[0])
            else:
                # Cetak amaran ke stderr supaya tidak mengganggu output kejayaan
                print(f"Amaran: Tiada wajah dikesan dalam {image_path}", file=sys.stderr)
        except Exception as e:
            print(f"Amaran: Tidak dapat memproses {image_path}: {e}", file=sys.stderr)

    if not all_encodings:
        return None
    return np.mean(all_encodings, axis=0)

def enroll_student_data(nama_pelajar, no_matrik):
    """Fungsi ini melakukan logik pendaftaran dan mengembalikan (Berjaya?, Mesej)."""
    conn = create_connection(DB_NAME)
    if not conn:
        return False, "Gagal menyambung ke pangkalan data."

    cursor = conn.cursor()
    cursor.execute("SELECT id_pelajar FROM pelajar WHERE no_matrik = ?", (no_matrik,))
    if cursor.fetchone():
        conn.close()
        return False, f"Ralat: Pelajar dengan nombor matrik '{no_matrik}' sudah wujud."

    safe_folder_name = re.sub(r'[\s\W]+', '_', nama_pelajar)
    student_image_folder = os.path.join(DATASET_BASE_DIR, safe_folder_name)
    
    if not os.path.isdir(student_image_folder):
        return False, f"Ralat: Folder gambar '{student_image_folder}' tidak ditemui. Pastikan anda telah menjalankan 'Ambil Gambar Wajah' dahulu untuk '{nama_pelajar}'."

    image_files = [os.path.join(student_image_folder, f) for f in os.listdir(student_image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not image_files:
        return False, f"Ralat: Tiada gambar ditemui dalam folder '{student_image_folder}'."

    representative_encoding = get_representative_encoding(image_files)
    if representative_encoding is None:
        return False, f"Gagal mendapatkan encoding wajah untuk '{nama_pelajar}'. Pastikan gambar yang diambil berkualiti dan jelas."
    
    os.makedirs(ENCODINGS_DIR, exist_ok=True)
    encoding_filepath = os.path.join(ENCODINGS_DIR, f"{no_matrik}.npy")
    np.save(encoding_filepath, representative_encoding)

    try:
        sql = '''INSERT INTO pelajar(nama_pelajar, no_matrik, path_encoding_wajah) VALUES(?,?,?)'''
        cursor.execute(sql, (nama_pelajar, no_matrik, encoding_filepath))
        conn.commit()
        message = f"Kejayaan: Pelajar '{nama_pelajar}' ({no_matrik}) berjaya didaftarkan."
        conn.close()
        return True, message
    except sqlite3.Error as e:
        conn.close()
        if os.path.exists(encoding_filepath):
            os.remove(encoding_filepath)
        return False, f"Ralat pangkalan data: {e}"

# ==============================================================================
# BLOK UTAMA YANG DIJALANKAN APABILA DIPANGGIL OLEH app.py
# ==============================================================================
if __name__ == '__main__':
    # Skrip ini perlukan 3 argumen: 
    # sys.argv[0] = enroll_student.py (nama skrip)
    # sys.argv[1] = nama_pelajar
    # sys.argv[2] = no_matrik
    if len(sys.argv) != 3:
        # Hantar mesej ralat ke stderr supaya Flask boleh tangkap sebagai ralat
        print("Penggunaan: python enroll_student.py \"Nama Pelajar\" \"NoMatrik\"", file=sys.stderr)
        sys.exit(1) # Keluar dengan kod ralat

    nama_pelajar_arg = sys.argv[1]
    no_matrik_arg = sys.argv[2]
    
    # Panggil fungsi utama dengan argumen yang diterima
    success, message = enroll_student_data(nama_pelajar_arg, no_matrik_arg)

    if success:
        # Jika berjaya, cetak mesej ke stdout. Flask akan tangkap ini sebagai mesej kejayaan.
        print(message)
        sys.exit(0) # Keluar dengan kod kejayaan
    else:
        # Jika gagal, cetak mesej ke stderr. Flask akan tangkap ini sebagai ralat.
        print(message, file=sys.stderr)
        sys.exit(1) # Keluar dengan kod ralat
