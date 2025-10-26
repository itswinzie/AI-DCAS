# delete_student.py (Versi Robust dengan Pemadaman Manual)
import sqlite3
import os
import sys

DB_NAME = "attendance_system.db"

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(f"DB Error: {e}", file=sys.stderr)
    return conn

def delete_student_by_no_matrik(no_matrik_to_delete):
    """
    Fungsi ini memadam pelajar dan data berkaitan secara manual,
    tanpa bergantung pada ON DELETE CASCADE.
    """
    conn = create_connection(DB_NAME)
    if not conn:
        return False, "Gagal menyambung ke pangkalan data."

    try:
        cursor = conn.cursor()

        # Langkah 1: Dapatkan id_pelajar dan path fail encoding
        cursor.execute("SELECT id_pelajar, path_encoding_wajah FROM pelajar WHERE no_matrik = ?", (no_matrik_to_delete,))
        result = cursor.fetchone()
        
        if not result:
            return False, f"Ralat: Pelajar dengan nombor matrik '{no_matrik_to_delete}' tidak ditemui."
        
        student_id, path_encoding_to_delete = result

        # Langkah 2: Padam rekod dari jadual 'kehadiran' terlebih dahulu (MANUAL CASCADE)
        cursor.execute("DELETE FROM kehadiran WHERE id_pelajar = ?", (student_id,))
        kehadiran_deleted_count = cursor.rowcount
        print(f"Info: {kehadiran_deleted_count} rekod kehadiran dipadam untuk pelajar ID {student_id}.", file=sys.stderr)

        # Langkah 3: Sekarang, padam rekod dari jadual 'pelajar'
        cursor.execute("DELETE FROM pelajar WHERE no_matrik = ?", (no_matrik_to_delete,))
        pelajar_deleted_count = cursor.rowcount

        conn.commit() # Lakukan commit selepas semua operasi delete berjaya

        if pelajar_deleted_count > 0:
            message = f"Kejayaan: Pelajar '{no_matrik_to_delete}' dan {kehadiran_deleted_count} rekod kehadiran berjaya dipadam."
            
            # Cuba padam fail encoding
            if path_encoding_to_delete and os.path.exists(path_encoding_to_delete):
                try:
                    os.remove(path_encoding_to_delete)
                    message += " Fail encoding juga berjaya dipadam."
                except OSError as e:
                    print(f"Amaran: Gagal memadam fail encoding '{path_encoding_to_delete}': {e}", file=sys.stderr)
            
            return True, message
        else:
            return False, "Gagal memadam rekod pelajar selepas memadam kehadiran. Sesuatu yang pelik berlaku."

    except sqlite3.Error as e:
        # Jika ada sebarang ralat, batalkan semua perubahan
        conn.rollback()
        return False, f"Ralat pangkalan data: {e}"
    finally:
        if conn:
            conn.close()

# Blok __main__ tidak perlu diubah, ia sudah betul
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Penggunaan: python delete_student.py \"NoMatrik\"", file=sys.stderr)
        sys.exit(1)

    no_matrik_arg = sys.argv[1]
    success, message = delete_student_by_no_matrik(no_matrik_arg)

    if success:
        print(message)
        sys.exit(0)
    else:
        print(message, file=sys.stderr)
        sys.exit(1)
