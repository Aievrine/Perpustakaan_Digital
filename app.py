from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'rahasia123'  # Ganti dengan secret key yang aman

# Koneksi database
DATABASE = 'database/perpustakaan.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Halaman Utama
@app.route('/')
def index():
    return redirect(url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama = request.form['nama']
        nis = request.form['nis']
        alamat = request.form['alamat']

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password, nama, nis, alamat, role) VALUES (?, ?, ?, ?, ?, ?)',
                           (username, password, nama, nis, alamat, 'siswa'))
            conn.commit()
            flash('Berhasil daftar! Silakan login.')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan!')
        finally:
            conn.close()

    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin_home'))
            else:
                return redirect(url_for('siswa_home'))
        else:
            flash('Login gagal. Cek kembali username dan password.')

    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Berhasil logout.')
    return redirect(url_for('login'))

# Helper function to get current user
def get_current_user():
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        return user
    return None

# Admin Dashboard
@app.route('/admin')
def admin_home():
    user = get_current_user()
    if not user or user['role'] != 'admin':
        flash('Silakan login sebagai admin.')
        return redirect(url_for('login'))
    return render_template('admin_home.html', current_user=user)

# Student Dashboard
@app.route('/siswa')
def siswa_home():
    user = get_current_user()
    if not user or user['role'] != 'siswa':
        flash('Silakan login sebagai siswa.')
        return redirect(url_for('login'))
    return render_template('siswa_home.html', current_user=user)

# Book List
@app.route('/daftar-buku')
def daftar_buku():
    user = get_current_user()
    if not user or user['role'] != 'siswa':
        flash('Silakan login sebagai siswa.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    books = conn.execute('SELECT * FROM buku WHERE stok > 0').fetchall()
    conn.close()
    return render_template('daftar_buku.html', books=books, current_user=user)

# Borrow Book
@app.route('/pinjam/<int:book_id>', methods=['POST'])
def pinjam_buku(book_id):
    user = get_current_user()
    if not user or user['role'] != 'siswa':
        flash('Silakan login sebagai siswa.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check book availability
    book = conn.execute('SELECT * FROM buku WHERE id = ?', (book_id,)).fetchone()
    if not book or book['stok'] <= 0:
        flash('Buku tidak tersedia.')
        return redirect(url_for('daftar_buku'))
    
    # Reduce stock
    conn.execute('UPDATE buku SET stok = stok - 1 WHERE id = ?', (book_id,))
    
    # Record borrowing
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    conn.execute('INSERT INTO peminjaman (user_id, buku_id, tanggal_pinjam) VALUES (?, ?, ?)',
                (user['id'], book_id, today))
    
    conn.commit()
    conn.close()
    
    flash('✅ Peminjaman berhasil! Silakan ambil buku di perpustakaan maksimal 2 hari.')
    return redirect(url_for('pinjam_sukses', book_id=book_id))

@app.route('/pinjam-sukses/<int:book_id>')
def pinjam_sukses(book_id):
    user = get_current_user()
    if not user or user['role'] != 'siswa':
        flash('Silakan login sebagai siswa.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    book = conn.execute('SELECT * FROM buku WHERE id = ?', (book_id,)).fetchone()
    conn.close()
    
    return render_template('pinjam_sukses.html', book=book, current_user=user)

@app.route('/riwayat-siswa')
def riwayat_siswa():
    user = get_current_user()
    if not user or user['role'] != 'siswa':
        flash('Silakan login sebagai siswa.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get active borrowings
    peminjaman = conn.execute('''
        SELECT p.id, b.judul, p.tanggal_pinjam, p.status_ambil 
        FROM peminjaman p
        JOIN buku b ON p.buku_id = b.id
        WHERE p.user_id = ?
    ''', (user['id'],)).fetchall()
    
    # Get borrowing history
    riwayat = conn.execute('''
        SELECT r.id, b.judul, r.tanggal_pinjam, r.tanggal_kembali
        FROM riwayat_peminjaman r
        JOIN buku b ON r.buku_id = b.id
        WHERE r.user_id = ?
    ''', (user['id'],)).fetchall()
    
    conn.close()
    
    return render_template('riwayat_siswa.html', 
                         peminjaman=peminjaman,
                         riwayat=riwayat,
                         current_user=user)

@app.route('/edit-profil', methods=['GET', 'POST'])
def edit_profil():
    user = get_current_user()
    if not user:
        flash('Silakan login terlebih dahulu.')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nama = request.form['nama']
        kelas = request.form['kelas']
        alamat = request.form['alamat']
        password = request.form['password']
        
        conn = get_db_connection()
        
        # Handle file upload
        foto = None
        if 'foto' in request.files:
            file = request.files['foto']
            if file.filename != '':
                # Save file to static/uploads
                filename = f"user_{user['id']}_{file.filename}"
                file.save(os.path.join('static/uploads', filename))
                foto = f"uploads/{filename}"
        
        # Update user data
        try:
            if password:
                conn.execute('''
                    UPDATE users SET 
                    nama = ?, kelas = ?, alamat = ?, password = ?, foto = COALESCE(?, foto)
                    WHERE id = ?
                ''', (nama, kelas, alamat, password, foto, user['id']))
            else:
                conn.execute('''
                    UPDATE users SET 
                    nama = ?, kelas = ?, alamat = ?, foto = COALESCE(?, foto)
                    WHERE id = ?
                ''', (nama, kelas, alamat, foto, user['id']))
            
            conn.commit()
            flash('Profil berhasil diperbarui!')
            return redirect(url_for('siswa_home'))
        except Exception as e:
            flash(f'Error: {str(e)}')
        finally:
            conn.close()
    
    return render_template('edit_profil.html', current_user=user)

if __name__ == '__main__':
    app.run(debug=True)
