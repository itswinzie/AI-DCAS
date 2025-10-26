import sqlite3
import face_recognition
import numpy as np
import cv2
import os
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO
import traceback

class AttendanceSystem:
    def __init__(self):
        self.DB_NAME = "attendance_system.db"
        self.STREAM_URL = "http://192.168.10.1:8000/video"
        self.WINDOW_NAME = 'Sistem Pengecaman Wajah Kehadiran'
        self.TOTAL_SCREEN_WIDTH, self.SCREEN_HEIGHT = 1600, 900
        self.STUDENT_LIST_PANEL_WIDTH = 500
        self.VIDEO_AREA_WIDTH = self.TOTAL_SCREEN_WIDTH - self.STUDENT_LIST_PANEL_WIDTH
        self.PANEL_INFO_HEIGHT = 200
        self.MAX_STUDENTS_IN_DISPLAY_LIST = 7
        self.FACE_MATCHING_TOLERANCE = 0.45
        
        # [PERUBAHAN] Menala ambang untuk pengesanan yang lebih baik
        self.EAR_THRESHOLD = 0.25      # Naikkan sedikit untuk lebih sensitiviti
        self.EAR_CONSEC_FRAMES = 2     # Kurangkan frame untuk pengesanan lebih pantas
        
        self.known_face_encodings, self.known_face_info_all, self.known_face_info_reco = [], [], []
        self.session_present_ids, self.scanned_students_list, self.face_blink_counters = set(), [], {}
        self.COLOR_BG_PANEL, self.COLOR_TEXT_HEADER = (40, 40, 40), (255, 255, 255)
        self.COLOR_TEXT_PRESENT, self.COLOR_TEXT_ABSENT = (0, 255, 0), (200, 200, 200)
        self.COLOR_BOX_PRESENT, self.COLOR_BOX_LIVENESS, self.COLOR_BOX_UNKNOWN = (0, 255, 0), (0, 255, 255), (0, 0, 255)
        self.CHECK_MARK, self.CROSS_MARK = "[HADIR]", "[BELUM]"

    def create_connection(self):
        try: return sqlite3.connect(self.DB_NAME)
        except sqlite3.Error as e: print(f"❌ Ralat sambungan DB: {e}"); return None

    def load_known_faces_from_db(self):
        print("🔄 Memuatkan data wajah...")
        conn = self.create_connection()
        if not conn: return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id_pelajar, nama_pelajar, no_matrik, path_encoding_wajah FROM pelajar")
            records = cursor.fetchall()
            self.known_face_encodings.clear(); self.known_face_info_all.clear(); self.known_face_info_reco.clear()
            for id_pelajar, nama, no_matrik, path in records:
                student_info = {"id": id_pelajar, "nama": nama, "no_matrik": no_matrik or "N/A"}
                self.known_face_info_all.append(student_info)
                if path and os.path.exists(path):
                    try:
                        encoding = np.load(path)
                        self.known_face_encodings.append(encoding); self.known_face_info_reco.append(student_info)
                    except Exception as e: print(f"⚠️ Gagal memuatkan encoding untuk {nama}: {e}")
            print(f"✅ Data dimuatkan: {len(self.known_face_encodings)} wajah dikenali.")
        finally: conn.close()

    def record_attendance(self, student_id):
        if student_id in self.session_present_ids:
            return False
        conn = self.create_connection()
        if not conn: 
            return False
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO kehadiran(id_pelajar, masa_masuk) VALUES (?, datetime('now', 'localtime'))", (student_id,))
            conn.commit()
            self.session_present_ids.add(student_id)
            info = next((i for i in self.known_face_info_reco if i["id"] == student_id), None)
            if info:
                self.scanned_students_list.insert(0, {"nama": info["nama"], "no_matrik": info["no_matrik"], "timestamp": datetime.now().strftime("%H:%M:%S")})
                self.scanned_students_list = self.scanned_students_list[:self.MAX_STUDENTS_IN_DISPLAY_LIST]
            
            try:
                url = "http://192.168.10.1:5000/trigger-relay"
                print(f"🚀 Menghantar arahan ke Raspberry Pi di {url}...")
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print("✅ Arahan berjaya dihantar dan diterima oleh Raspberry Pi.")
                else:
                    print(f"⚠️ Ralat dari server Raspberry Pi: {response.status_code} - {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"‼️ Gagal menyambung ke Raspberry Pi: {e}")
            return True
        except sqlite3.Error as e:
            print(f"❌ Ralat semasa merekod kehadiran: {e}"); return False
        finally:
            if conn: conn.close()

    def _calculate_ear(self, eye):
        A = np.linalg.norm(np.array(eye[1]) - np.array(eye[5])); B = np.linalg.norm(np.array(eye[2]) - np.array(eye[4])); C = np.linalg.norm(np.array(eye[0]) - np.array(eye[3]))
        return (A + B) / (2.0 * C)

    def draw_detected_students_panel(self, canvas):
        y_start = self.SCREEN_HEIGHT - self.PANEL_INFO_HEIGHT; panel_width = self.VIDEO_AREA_WIDTH
        cv2.rectangle(canvas, (0, y_start), (panel_width, self.SCREEN_HEIGHT), self.COLOR_BG_PANEL, -1)
        cv2.putText(canvas, "KEHADIRAN TERKINI", (10, y_start + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_TEXT_HEADER, 2)
        y_pos = y_start + 55
        for student in self.scanned_students_list:
            text = f"{student['nama']} ({student['no_matrik']}) - {student['timestamp']}"
            cv2.putText(canvas, text, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.COLOR_TEXT_PRESENT, 1); y_pos += 25

    def draw_full_student_list_panel(self, canvas):
        x_start = self.VIDEO_AREA_WIDTH
        cv2.rectangle(canvas, (x_start, 0), (self.TOTAL_SCREEN_WIDTH, self.SCREEN_HEIGHT), self.COLOR_BG_PANEL, -1)
        cv2.putText(canvas, "SENARAI NAMA PELAJAR", (x_start + 10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.COLOR_TEXT_HEADER, 2)
        y_pos = 70
        for i, student in enumerate(self.known_face_info_all):
            is_present = student['id'] in self.session_present_ids
            status, color = (self.CHECK_MARK, self.COLOR_TEXT_PRESENT) if is_present else (self.CROSS_MARK, self.COLOR_TEXT_ABSENT)
            text = f"{status} {student['nama']}"
            cv2.putText(canvas, text, (x_start + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1); y_pos += 25
            if y_pos > self.SCREEN_HEIGHT - 20:
                if i < len(self.known_face_info_all) - 1: cv2.putText(canvas, "...", (x_start + 10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.COLOR_TEXT_HEADER, 1)
                break

    def run(self):
        self.load_known_faces_from_db()
        if not self.known_face_encodings: print("❌ KRITIKAL: Tiada data wajah sah."); return
        try:
            print(f"🔄 Menyambung ke stream MJPEG di: {self.STREAM_URL}"); stream = requests.get(self.STREAM_URL, stream=True, timeout=10); byte_data = b''
            print("✅ Sambungan ke stream berjaya.")
        except requests.exceptions.RequestException as e: print(f"❌ Gagal sambung ke stream MJPEG: {e}"); return
        cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL); cv2.resizeWindow(self.WINDOW_NAME, self.TOTAL_SCREEN_WIDTH, self.SCREEN_HEIGHT)
        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN); print("🟢 Memulakan pengecaman...")
        detection_scale = 0.25; display_h = self.SCREEN_HEIGHT - self.PANEL_INFO_HEIGHT; scale_x, scale_y = None, None
        try:
            for chunk in stream.iter_content(chunk_size=4096):
                byte_data += chunk; start = byte_data.find(b'\xff\xd8'); end = byte_data.find(b'\xff\xd9')
                if start == -1 or end == -1 or end <= start: continue
                jpg = byte_data[start:end+2]; byte_data = byte_data[end+2:]
                try: frame = cv2.cvtColor(np.array(Image.open(BytesIO(jpg))), cv2.COLOR_RGB2BGR)
                except Exception: continue
                if scale_x is None: h, w, _ = frame.shape; scale_x = self.VIDEO_AREA_WIDTH / w; scale_y = display_h / h
                small_frame = cv2.resize(frame, (0, 0), fx=detection_scale, fy=detection_scale)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                canvas = np.zeros((self.SCREEN_HEIGHT, self.TOTAL_SCREEN_WIDTH, 3), dtype=np.uint8)
                canvas[:display_h, :self.VIDEO_AREA_WIDTH] = cv2.resize(frame, (self.VIDEO_AREA_WIDTH, display_h))
                face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                face_landmarks_list = face_recognition.face_landmarks(rgb_small_frame, face_locations)
                current_face_keys = set(face_locations)
                for key in list(self.face_blink_counters.keys()):
                    if key not in current_face_keys: del self.face_blink_counters[key]
                for (top, right, bottom, left), face_encoding, face_landmarks in zip(face_locations, face_encodings, face_landmarks_list):
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    name, color = "Tidak Dikenali", self.COLOR_BOX_UNKNOWN
                    
                    # [PERUBAHAN] Sediakan pembolehubah untuk memaparkan nilai EAR
                    ear_to_display = None
                    
                    if face_distances[best_match_index] <= self.FACE_MATCHING_TOLERANCE:
                        info = self.known_face_info_reco[best_match_index]; student_id = info['id']
                        if student_id in self.session_present_ids:
                            name, color = info['nama'], self.COLOR_BOX_PRESENT
                        else:
                            name, color = f"{info['nama']} (Sila Kelip Mata)", self.COLOR_BOX_LIVENESS
                            ear = (self._calculate_ear(face_landmarks['left_eye']) + self._calculate_ear(face_landmarks['right_eye'])) / 2.0
                            
                            # [PERUBAHAN] Simpan nilai EAR untuk dipaparkan
                            ear_to_display = ear
                            
                            face_key = (top, right, bottom, left)
                            if ear < self.EAR_THRESHOLD:
                                self.face_blink_counters[face_key] = self.face_blink_counters.get(face_key, 0) + 1
                            else:
                                if self.face_blink_counters.get(face_key, 0) >= self.EAR_CONSEC_FRAMES:
                                    print(f"✅ Kelipan disahkan untuk {info['nama']}!"); self.record_attendance(student_id)
                                self.face_blink_counters[face_key] = 0
                                
                    l, t, r, b = int(left / detection_scale * scale_x), int(top / detection_scale * scale_y), int(right / detection_scale * scale_x), int(bottom / detection_scale * scale_y)
                    cv2.rectangle(canvas, (l, t), (r, b), color, 2); cv2.rectangle(canvas, (l, b - 25), (r, b), color, cv2.FILLED)
                    cv2.putText(canvas, name, (l + 6, b - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
                    
                    # [PERUBAHAN] Tambah paparan nilai EAR jika ia sedang dikira
                    if ear_to_display is not None:
                        cv2.putText(canvas, f"EAR: {ear_to_display:.2f}", (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

                self.draw_detected_students_panel(canvas); self.draw_full_student_list_panel(canvas); cv2.imshow(self.WINDOW_NAME, canvas)
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'): break
                elif key == ord('f'): cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                elif key == ord('n'): cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        finally:
            cv2.destroyAllWindows(); print("\n⏹️ Program dihentikan.")
            print("\n📊 ===== RUMUSAN SESI KEHADIRAN =====")
            if self.session_present_ids:
                print(f"Jumlah hadir: {len(self.session_present_ids)}/{len(self.known_face_info_all)}")
                for student in reversed(self.scanned_students_list): print(f"- {student['nama']} ({student['no_matrik']}) @ {student['timestamp']}")
            else: print("❗ Tiada kehadiran direkodkan.")

if __name__ == '__main__':
    try:
        system = AttendanceSystem()
        system.run()
    except Exception as e:
        print("\n\n" + "="*50 + "\n    ‼️   RALAT KRITIKAL   ‼️\n" + "="*50)
        print(f"RALAT: {e}"); print("\nButiran Teknikal:"); traceback.print_exc()
    finally: input("\nTekan Enter untuk keluar...")
