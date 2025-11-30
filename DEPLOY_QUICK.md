# ⚡ Quick Deployment Guide - WINSON

## 🎯 Info Penting
- **Port**: `9004`
- **Domain**: `winson.instagram-igs.my.id`
- **Repo**: `https://github.com/Winsonlearn/instagramresmi.git`

---

## 📝 Langkah Cepat

### 1️⃣ Terminal - Update Project (Sudah Pull)
```bash
cd /www/wwwroot/instagramresmi
chown -R www:www /www/wwwroot/instagramresmi
chmod -R 775 /www/wwwroot/instagramresmi
pip install -r requirements.txt
```

### 2️⃣ Python Manager - Add Project
- **Name**: `instagramresmi-winson`
- **Path**: `/www/wwwroot/instagramresmi`
- **Framework**: `Flask`
- **Startup**: `wsgi.py`
- **Port**: `9004` ⚠️
- **Command**: 
  ```bash
  cd /www/wwwroot/instagramresmi && pip install -r requirements.txt && gunicorn --worker-class eventlet -w 1 wsgi:app -b 127.0.0.1:9004
  ```

### 3️⃣ Website - Add Site
- **Domain**: `winson.instagram-igs.my.id`
- **Directory**: `/www/wwwroot/instagramresmi`
- Klik **ikon bulu burung** → **Reverse Proxy**

### 4️⃣ Reverse Proxy - Add Proxy
- **Target URL**: `http://127.0.0.1:9004` ⚠️
- **WebSocket**: ✅ Enable

### 5️⃣ Restart Apache

✅ **DONE!**

