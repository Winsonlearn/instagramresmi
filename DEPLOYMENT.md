# 🚀 Panduan Deployment VPS

## ✅ Langkah-langkah Setup di VPS

### 1. Masuk ke folder project
```bash
cd /www/wwwroot/instagramresmi
```

### 2. Pastikan semua file ada
```bash
ls -la
# Harus ada: wsgi.py, main.py, requirements.txt, app/
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup environment variables
Buat file `.env` di root project:
```bash
nano .env
```

Isi dengan:
```env
FLASK_DEBUG=
SECRET_KEY=your-secret-key-here-minimal-32-characters
DB_URI=sqlite:///instance/site.db
```

### 5. Inisialisasi database
```bash
python -c "from app import create_app; app = create_app(); from app.extension import db; db.create_all()"
```

### 6. Jalankan dengan Gunicorn
```bash
gunicorn --worker-class eventlet -w 1 wsgi:app -b 127.0.0.1:5000
```

**Catatan:** Aplikasi akan berjalan di `127.0.0.1:5000` (localhost). Web server (Nginx/Apache) harus dikonfigurasi untuk proxy ke port ini.

### 7. Setup sebagai service (systemd) - OPSIONAL

Buat file `/etc/systemd/system/instagramresmi.service`:
```ini
[Unit]
Description=Instagram Clone Gunicorn App
After=network.target

[Service]
User=www
Group=www
WorkingDirectory=/www/wwwroot/instagramresmi
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn --worker-class eventlet -w 1 wsgi:app -b 127.0.0.1:5000

[Install]
WantedBy=multi-user.target
```

Kemudian:
```bash
sudo systemctl daemon-reload
sudo systemctl enable instagramresmi
sudo systemctl start instagramresmi
sudo systemctl status instagramresmi
```

### 8. Konfigurasi Nginx (jika pakai Nginx)

Edit file konfigurasi Nginx untuk domain `winson.instagram-igs.my.id`:

```nginx
server {
    listen 80;
    server_name winson.instagram-igs.my.id;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support untuk SocketIO
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /static {
        alias /www/wwwroot/instagramresmi/app/static;
        expires 30d;
    }

    # Uploaded files
    location /uploads {
        alias /www/wwwroot/instagramresmi/uploads;
        expires 30d;
    }
}
```

Reload Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔍 Troubleshooting

### Cek apakah aplikasi berjalan
```bash
ps aux | grep gunicorn
netstat -tulpn | grep 5000
```

### Cek log error
```bash
# Jika pakai systemd
sudo journalctl -u instagramresmi -f

# Atau cek log langsung
tail -f /var/log/nginx/error.log
```

### Test aplikasi langsung
```bash
curl http://127.0.0.1:5000
```

### Cek permission folder
```bash
chmod -R 755 /www/wwwroot/instagramresmi
chown -R www:www /www/wwwroot/instagramresmi
```

---

## 📝 Catatan Penting

1. **Port 5000** harus diakses dari localhost saja (127.0.0.1), bukan 0.0.0.0
2. **Web server** (Nginx/Apache) harus dikonfigurasi untuk proxy ke port 5000
3. **Database** harus diinisialisasi sebelum pertama kali run
4. **Environment variables** (.env) harus disetup dengan benar
5. **SocketIO** memerlukan WebSocket support di Nginx

