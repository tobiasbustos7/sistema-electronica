#!/bin/bash
set -e

# ============================================================
# Script de despliegue - Sistema Electronica
# Ejecutar como root en el VPS
# ============================================================

DOMAIN="moviltec.lat"
APP_DIR="/home/sistema-electronica"
GIT_REPO="https://github.com/tobiasbustos7/sistema-electronica.git"

echo "=== Actualizando sistema ==="
apt update && apt upgrade -y

echo "=== Instalando dependencias ==="
apt install -y python3 python3-pip python3-venv nginx git mysql-server supervisor certbot python3-certbot-nginx

echo "=== Creando directorio de la aplicacion ==="
mkdir -p $APP_DIR
mkdir -p /var/log/sistema-electronica

echo "=== Clonando repositorio ==="
git clone $GIT_REPO $APP_DIR

echo "=== Creando entorno virtual ==="
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn pymysql cryptography mysqlclient

echo "=== Configurando MySQL ==="
mysql <<EOF
CREATE DATABASE IF NOT EXISTS electronica_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'electronica'@'localhost' IDENTIFIED BY 'electronica_pass_2025';
GRANT ALL PRIVILEGES ON electronica_db.* TO 'electronica'@'localhost';
FLUSH PRIVILEGES;
EOF

echo "=== Configurando variables de entorno ==="
cat > $APP_DIR/.env.prod <<EOF
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=mysql+pymysql://electronica:electronica_pass_2025@localhost/electronica_db
FLASK_ENV=production
EOF

echo "=== Configurando Nginx ==="
cp $APP_DIR/deploy/nginx-moviltec.lat.conf /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo "=== Configurando Supervisor ==="
cp $APP_DIR/deploy/supervisor-electronica.conf /etc/supervisor/conf.d/sistema-electronica.conf
sed -i "s|\$(cat.*)|$(grep SECRET_KEY $APP_DIR/.env.prod | cut -d= -f2-)|" /etc/supervisor/conf.d/sistema-electronica.conf
supervisorctl reread
supervisorctl update
supervisorctl start sistema-electronica

echo "=== Configurando SSL con Certbot ==="
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

echo ""
echo "=== DESPLIEGUE COMPLETADO ==="
echo "Tu sistema esta disponible en: https://$DOMAIN"
echo ""
echo "Para ver logs: sudo supervisorctl tail -f sistema-electronica"
echo "Para reiniciar: sudo supervisorctl restart sistema-electronica"
