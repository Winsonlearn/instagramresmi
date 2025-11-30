#!/bin/bash

# Setup script untuk deployment di VPS
# Jalankan setelah git pull

echo "🚀 Setting up Instagram Clone Project..."

# Navigate ke project directory
cd /www/wwwroot/instagramresmi || exit

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔧 Setting permissions..."
chown -R www:www /www/wwwroot/instagramresmi
chmod -R 775 /www/wwwroot/instagramresmi

echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Go to Python Manager in AA Panel"
echo "2. Add new project with port 9004"
echo "3. Setup website: winson.instagram-igs.my.id"
echo "4. Configure reverse proxy to http://127.0.0.1:9004"
echo "5. Restart Apache"

