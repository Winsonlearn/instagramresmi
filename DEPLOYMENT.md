# 🚀 Deployment Guide untuk AA Panel

## 📋 Informasi Project

- **Repository**: https://github.com/Winsonlearn/instagramresmi.git
- **Port untuk Winson**: `9004`
- **Domain**: `winson.instagram-igs.my.id`
- **Project Path**: `/www/wwwroot/instagramresmi`

---

## ✅ Langkah-langkah Deployment

### 1. Login ke AA Panel

- **Link**: https://103.245.38.109:28233/03f7a70e
- **Username**: zzgvwppt
- **Password**: a3a577e8

---

### 2. Clone Project di Terminal

Masuk ke **Terminal** di AA Panel, lalu jalankan:

```bash
cd /www/wwwroot
git clone https://github.com/Winsonlearn/instagramresmi.git instagramresmi
chown -R www:www instagramresmi
chmod -R 775 instagramresmi
```

---

### 3. Setup Python Project

Masuk ke **Python Manager** → **Add Project**

**Konfigurasi Project:**

- **Project Name**: `instagramresmi-winson` (atau nama lain yang unik)
- **Python Version**: `3.12` (atau sesuai yang tersedia)
- **Project Path**: `/www/wwwroot/instagramresmi`
- **Framework**: `Flask`
- **Startup File**: `wsgi.py`
- **Port**: `9004` ⚠️ **PENTING: Port untuk Winson adalah 9004**
- **Run User**: `www`

**Command untuk Run:**

```bash
cd /www/wwwroot/instagramresmi
pip install -r requirements.txt
gunicorn --worker-class eventlet -w 1 wsgi:app -b 127.0.0.1:9004
```

**⚠️ NOTICE**: 
- Jika ada pop-up, **JANGAN di-refresh atau di-tutup**, biarkan dulu
- Pastikan port **9004** (untuk Winson) tidak digunakan oleh project lain

---

### 4. Setup Website

Masuk ke **Website** → **Add Site**

**Konfigurasi Website:**

- **Domain**: `winson.instagram-igs.my.id`
- **Site Directory**: `/www/wwwroot/instagramresmi`
- **PHP Version**: Tidak perlu (karena ini Python Flask)

Setelah website dibuat, klik **ikon bulu burung** di domain untuk masuk ke pengaturan.

---

### 5. Setup Reverse Proxy

Di halaman website, masuk ke bagian **Reverse Proxy** → **Add Proxy**

**Konfigurasi Reverse Proxy:**

- **Domain**: `winson.instagram-igs.my.id`
- **Target URL**: `http://127.0.0.1:9004` ⚠️ **PASTIKAN PORT 9004**
- **Send Domain**: ✅ Centang
- **WebSocket**: ✅ Centang (penting untuk SocketIO)

**⚠️ PENTING**: 
- Target URL harus `http://127.0.0.1:9004` (bukan port lain)
- WebSocket harus diaktifkan karena aplikasi menggunakan Flask-SocketIO

---

### 6. Restart Apache

Setelah semua konfigurasi selesai, **RESTART APACHE** di AA Panel.

---

## 🔍 Verifikasi Deployment

Setelah deployment, cek:

1. **Python App Running**: Pastikan di Python Manager status project adalah "Running"
2. **Website Accessible**: Buka `https://winson.instagram-igs.my.id` di browser
3. **SocketIO Working**: Test fitur real-time (chat, notifications) apakah berfungsi

---

## 📝 Checklist Deployment

- [ ] Login ke AA Panel
- [ ] Clone project dari GitHub
- [ ] Set permissions (chown & chmod)
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Buat Python Project di Python Manager (Port: 9004)
- [ ] Buat Website dengan domain `winson.instagram-igs.my.id`
- [ ] Setup Reverse Proxy ke `http://127.0.0.1:9004`
- [ ] Enable WebSocket di Reverse Proxy
- [ ] Restart Apache
- [ ] Test website di browser

---

## 🐛 Troubleshooting

### Port sudah digunakan
- Cek port lain yang tersedia atau hentikan aplikasi yang menggunakan port 9004

### SocketIO tidak bekerja
- Pastikan WebSocket diaktifkan di Reverse Proxy
- Pastikan menggunakan `eventlet` worker: `--worker-class eventlet`

### Permission denied
- Pastikan menjalankan: `chown -R www:www instagramresmi` dan `chmod -R 775 instagramresmi`

### Dependencies error
- Pastikan Python version >= 3.12
- Install ulang: `pip install -r requirements.txt --upgrade`

---

## 📌 Catatan Penting

1. **Port Assignment**:
   - 9001: KEVIN
   - 9002: KEVIN-TEST
   - 9003: VINO
   - 9004: **WINSON** ← Port kamu
   - 9005: LEWIS
   - 9006: ARTHA
   - 9007: DANIELE

2. **Domain yang Diizinkan**:
   - `lewis.instagram-igs.my.id`
   - `artha.instagram-igs.my.id`
   - `vino.instagram-igs.my.id`
   - `winson.instagram-igs.my.id` ← Domain kamu
   - `daniele.instagram-igs.my.id`

3. **Jangan**:
   - Menggunakan port yang sudah dipakai orang lain
   - Menggunakan domain selain yang ada di list
   - Menghapus atau mengubah project orang lain di Python Manager

---

## 🔗 Link Penting

- **AA Panel**: https://103.245.38.109:28233/03f7a70e
- **GitHub Repo**: https://github.com/Winsonlearn/instagramresmi.git
- **Domain**: https://winson.instagram-igs.my.id

