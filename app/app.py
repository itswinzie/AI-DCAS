# app.py (Versi Akhir: Gabungan Demo & Laporan dengan Fungsi Reset)

from flask import Flask, render_template, request, flash, redirect, url_for, g, Response
import subprocess
import os
import sys
import sqlite3
from datetime import datetime
import io
import csv

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kunci-rahsia-super-selamat-untuk-projek-dcas'
DATABASE = "attendance_system.db"

# --- Pengenalpastian Jenis Skrip ---
GUI_SCRIPTS = {"capture_images.py", "recognize_faces.py"}
ALLOWED_SCRIPTS = {
    "recognize_faces.py": "Mula Pengecaman Wajah",
    "capture_images.py": "Ambil Gambar Wajah",
    "enroll_student.py": "Daftarkan Pelajar",
    "delete_student.py": "Padam Pelajar"
}

# --- Fungsi Utiliti Pangkalan Data ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# [BARU] Fungsi khas untuk mengubah data (DELETE, INSERT, UPDATE)
def modify_db(query, args=()):
    db = get_db()
    db.execute(query, args)
    db.commit()

# --- Laluan (Routes) untuk Panel Kawalan & Tindakan ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    script_name = request.form.get('script')
    if not script_name or script_name not in ALLOWED_SCRIPTS:
        flash(f"Operasi tidak dibenarkan untuk skrip '{script_name}'.", "error")
        return redirect(url_for('index'))
    command = [sys.executable, script_name]
    nama_pelajar = request.form.get('nama_pelajar')
    no_matrik = request.form.get('no_matrik')
    if script_name == "capture_images.py":
        if not nama_pelajar:
            flash("Nama pelajar diperlukan untuk mengambil gambar.", "error"); return redirect(url_for('index'))
        command.append(nama_pelajar)
    elif script_name == "enroll_student.py":
        if not nama_pelajar or not no_matrik:
            flash("Nama dan No. Matrik diperlukan untuk mendaftar.", "error"); return redirect(url_for('index'))
        command.extend([nama_pelajar, no_matrik])
    elif script_name == "delete_student.py":
        if not no_matrik:
            flash("No. Matrik diperlukan untuk memadam.", "error"); return redirect(url_for('index'))
        command.append(no_matrik)
    try:
        if script_name in GUI_SCRIPTS:
            my_env = os.environ.copy(); my_env["DISPLAY"] = ":0"
            subprocess.Popen(command, env=my_env)
            flash(f"Skrip '{ALLOWED_SCRIPTS[script_name]}' telah dimulakan.", "success")
        else:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            flash(result.stdout.strip() or "Operasi selesai.", "success")
    except subprocess.CalledProcessError as e:
        flash(f"Ralat dari skrip '{script_name}': {e.stderr.strip()}", "error")
    except FileNotFoundError:
        flash(f"Ralat Kritikal: Skrip '{script_name}' tidak ditemui.", "error")
    except Exception as e:
        flash(f"Ralat tidak dijangka: {e}", "error")
    return redirect(url_for('index'))

# --- Laluan (Routes) untuk Laporan Kehadiran ---

@app.route('/laporan')
def dashboard():
    all_students = query_db("SELECT id_pelajar, nama_pelajar, no_matrik FROM pelajar ORDER BY nama_pelajar ASC")
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_attendance_records = query_db("""
        SELECT p.id_pelajar, p.nama_pelajar, p.no_matrik, MIN(k.masa_masuk) as masa_masuk_pertama 
        FROM kehadiran k JOIN pelajar p ON k.id_pelajar = p.id_pelajar
        WHERE date(k.masa_masuk) = ? 
        GROUP BY p.id_pelajar ORDER BY masa_masuk_pertama ASC
    """, (today_str,))
    attended_today_ids = {record['id_pelajar'] for record in todays_attendance_records}
    return render_template('dashboard.html', 
                           all_students=all_students, 
                           todays_attendance_list=todays_attendance_records,
                           attended_today_ids=attended_today_ids,
                           current_date=datetime.now().strftime('%A, %d %B %Y'))

@app.route('/download_csv')
def download_csv():
    today_str = datetime.now().strftime('%Y-%m-%d')
    attendance_data = query_db("""
        SELECT p.nama_pelajar, p.no_matrik, strftime('%H:%M:%S', k.masa_masuk) as waktu_masuk
        FROM kehadiran k JOIN pelajar p ON k.id_pelajar = p.id_pelajar
        WHERE date(k.masa_masuk) = ? ORDER BY k.masa_masuk ASC
    """, (today_str,))
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Bil.', 'Nama Pelajar', 'No Matrik', 'Waktu Masuk'])
    for i, row in enumerate(attendance_data):
        cw.writerow([i+1, row['nama_pelajar'], row['no_matrik'], row['waktu_masuk']])
    output = si.getvalue()
    return Response(output, mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename=kehadiran_{today_str}.csv"})

# [BARU] Laluan (Route) untuk butang Reset
@app.route('/reset_today', methods=['POST'])
def reset_today_attendance():
    today_str = datetime.now().strftime('%Y-%m-%d')
    modify_db("DELETE FROM kehadiran WHERE date(masa_masuk) = ?", (today_str,))
    flash('Semua rekod kehadiran untuk hari ini telah berjaya direset.', 'success')
    # Halakan pengguna kembali ke halaman laporan
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("Sistem AI-DCAS (Mod Pembentangan + Laporan) sedia di http://127.0.0.1:5000")
    print("Tekan CTRL+C untuk berhenti.")
    app.run(host='0.0.0.0', port=5000, debug=True)
