from flask import Flask, Response
import cv2
import numpy as np

app = Flask(__name__)

def create_error_frame():
    # Cipta imej hitam sebagai placeholder ralat
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Tulis teks ralat pada imej
    cv2.putText(frame, "Kamera Gagal Dibuka", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    ret, buffer = cv2.imencode('.jpg', frame)
    return buffer.tobytes()

def gen_frames():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Kamera gagal dibuka")
        # Hantar satu frame ralat dan berhenti
        error_frame = create_error_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + error_frame + b'\r\n')
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Gagal baca frame")
            break

        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    cap.release()

@app.route('/video')
def video():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
