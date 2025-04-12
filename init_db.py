import sqlite3

# Koneksi ke database
conn = sqlite3.connect('database/perpustakaan.db')
c = conn.cursor()

# Tabel users
c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        nama TEXT NOT NULL,
        nis TEXT NOT NULL UNIQUE,
        kelas TEXT,
        alamat TEXT,
        foto TEXT,
        role TEXT NOT NULL CHECK (role IN ('siswa', 'admin'))
    )
''')

# Tabel buku
c.execute('''
    CREATE TABLE IF NOT EXISTS buku (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        judul TEXT NOT NULL,
        penulis TEXT,
        penerbit TEXT,
        tahun TEXT,
        stok INTEGER NOT NULL
    )
''')

# Tabel peminjaman (yang sedang berlangsung)
c.execute('''
    CREATE TABLE IF NOT EXISTS peminjaman (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        buku_id INTEGER,
        tanggal_pinjam TEXT,
        status_ambil TEXT DEFAULT 'belum',  -- 'belum' atau 'sudah'
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(buku_id) REFERENCES buku(id)
    )
''')

# Tabel riwayat_peminjaman (riwayat setelah dikembalikan)
c.execute('''
    CREATE TABLE IF NOT EXISTS riwayat_peminjaman (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        buku_id INTEGER,
        tanggal_pinjam TEXT,
        tanggal_kembali TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(buku_id) REFERENCES buku(id)
    )
''')

conn.commit()
conn.close()
print("Semua tabel berhasil dibuat.")
