from flask import Flask, render_template, Response, g, redirect, url_for, flash
import sqlite3
from datetime import datetime
import io
import csv

DATABASE = "attendance_system.db"

app = Flask(__name__)

# [BARU] Tambah 'secret_key'. Ini PENTING untuk fungsi 'flash'.
# Tukar 'kunci_rahsia_anda' kepada apa-apa frasa rawak yang anda suka.
app.secret_key = 'kunci_rahsia_yang_selamat_dan_rawak'

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

@app.route('/')
def dashboard():
    all_students = query_db("SELECT id_pelajar, nama_pelajar, no_matrik FROM pelajar ORDER BY nama_pelajar ASC")
    today_str = datetime.now().strftime('%Y-%m-%d')
    todays_attendance_records = query_db("""
        SELECT 
            p.id_pelajar, p.nama_pelajar, p.no_matrik, 
            MIN(k.masa_masuk) as masa_masuk_pertama 
        FROM kehadiran k
        JOIN pelajar p ON k.id_pelajar = p.id_pelajar
        WHERE date(k.masa_masuk) = ? 
        GROUP BY p.id_pelajar
        ORDER BY masa_masuk_pertama ASC
    """, (today_str,))
    attended_today_ids = {record['id_pelajar'] for record in todays_attendance_records}
    return render_template('dashboard.html', 
                           all_students=all_students, 
                           todays_attendance_list=todays_attendance_records,
                           attended_today_ids=attended_today_ids,
                           current_date=datetime.now().strftime('%A, %d %B %Y'))

@app.route('/download_attendance_csv')
def download_attendance_csv():
    today_str = datetime.now().strftime('%Y-%m-%d')
    attendance_data = query_db("""
        SELECT p.nama_pelajar, p.no_matrik, strftime('%H:%M:%S', MIN(k.masa_masuk)) as waktu_masuk
        FROM kehadiran k
        JOIN pelajar p ON k.id_pelajar = p.id_pelajar
        WHERE date(k.masa_masuk) = ?
        GROUP BY p.id_pelajar
        ORDER BY k.masa_masuk ASC
    """, (today_str,))
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Bil.', 'Nama Pelajar', 'No Matrik', 'Waktu Masuk'])
    for i, row in enumerate(attendance_data):
        cw.writerow([i+1, row['nama_pelajar'], row['no_matrik'], row['waktu_masuk']])
    output = si.getvalue()
    si.close()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=kehadiran_{today_str}.csv"})

# [BARU] Laluan (Route) untuk butang Reset
@app.route('/reset_today', methods=['POST'])
def reset_today_attendance():
    """
    Fungsi ini akan memadam semua rekod kehadiran untuk hari ini.
    Ia hanya boleh diakses melalui kaedah POST untuk keselamatan.
    """
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Laksanakan arahan DELETE pada pangkalan data
    modify_db("DELETE FROM kehadiran WHERE date(masa_masuk) = ?", (today_str,))
    
    # Hantar mesej maklum balas kepada pengguna
    flash('Semua rekod kehadiran untuk hari ini telah berjaya direset.', 'success')
    
    # Halakan pengguna kembali ke halaman utama
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
