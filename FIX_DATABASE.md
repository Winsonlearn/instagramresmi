# 🔧 Fix Database Configuration Error

## ❌ Error yang Terjadi

```
RuntimeError: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.
```

## ✅ Solusi

### Opsi 1: Gunakan SQLite (Paling Mudah - Sudah Diperbaiki di Code)

Aplikasi sekarang **otomatis** akan menggunakan SQLite jika `DB_URI` tidak diset di environment variable.

Database akan dibuat di: `/www/wwwroot/instagramresmi/instance/site.db`

**Tidak perlu setup tambahan!** Cukup restart Gunicorn.

---

### Opsi 2: Set Environment Variable (Jika Pakai MySQL/PostgreSQL)

#### A. Via File `.env` di Root Project

Buat/edit file `.env` di `/www/wwwroot/instagramresmi/.env`:

```env
FLASK_DEBUG=
SECRET_KEY=your-secret-key-here-minimal-32-characters
DB_URI=sqlite:///instance/site.db
```

**Untuk SQLite (default):**
```env
DB_URI=sqlite:////www/wwwroot/instagramresmi/instance/site.db
```

**Untuk MySQL:**
```env
DB_URI=mysql+pymysql://username:password@localhost/database_name
```

**Untuk PostgreSQL:**
```env
DB_URI=postgresql://username:password@localhost/database_name
```

#### B. Via Panel (aaPanel/BT Panel)

1. Buka konfigurasi Gunicorn service
2. Cari **Environment Variables** atau **Config**
3. Tambahkan:
   - **Key:** `DB_URI`
   - **Value:** `sqlite:////www/wwwroot/instagramresmi/instance/site.db`

---

## 🚀 Setelah Fix, Restart Gunicorn

```bash
# Jika pakai systemd
sudo systemctl restart instagramresmi

# Atau restart via panel
```

---

## ✅ Verifikasi

Setelah restart, cek log:
```bash
sudo journalctl -u instagramresmi -f
```

Seharusnya tidak ada error `SQLALCHEMY_DATABASE_URI` lagi.

---

## 📝 Catatan

- **SQLite** sudah cukup untuk development/testing
- Untuk production dengan traffic tinggi, gunakan **MySQL** atau **PostgreSQL**
- Pastikan folder `instance/` ada dan writable:
  ```bash
  mkdir -p /www/wwwroot/instagramresmi/instance
  chmod 755 /www/wwwroot/instagramresmi/instance
  ```

