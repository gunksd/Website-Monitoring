#!/bin/bash

# Nginx配置脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Nginx配置脚本 ===${NC}"

# 检查是否为root用户
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}此脚本需要root权限，请使用sudo运行${NC}"
    exit 1
fi

# 获取用户输入
read -p "请输入您的域名 (例如: example.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}域名不能为空${NC}"
    exit 1
fi

# 检查Nginx是否安装
if ! command -v nginx &> /dev/null; then
    echo -e "${YELLOW}Nginx未安装，正在安装...${NC}"
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$NAME" == *"Ubuntu"* ]] || [[ "$NAME" == *"Debian"* ]]; then
            apt update && apt install -y nginx
        elif [[ "$NAME" == *"CentOS"* ]] || [[ "$NAME" == *"Red Hat"* ]]; then
            yum install -y nginx
        fi
    fi
fi

# 创建配置文件
NGINX_CONF="/etc/nginx/sites-available/website-monitor"
NGINX_ENABLED="/etc/nginx/sites-enabled/website-monitor"

echo -e "${YELLOW}创建Nginx配置文件...${NC}"

# 复制并修改配置文件
cp website-monitor.conf "$NGINX_CONF"
sed -i "s/your-domain.com/$DOMAIN/g" "$NGINX_CONF"

# 询问是否配置SSL
read -p "是否已有SSL证书？(y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "请输入证书文件路径 (例如: /etc/ssl/certs/your-cert.crt): " CERT_PATH
    read -p "请输入私钥文件路径 (例如: /etc/ssl/private/your-key.key): " KEY_PATH

    if [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
        sed -i "s|/path/to/your/certificate.crt|$CERT_PATH|g" "$NGINX_CONF"
        sed -i "s|/path/to/your/private.key|$KEY_PATH|g" "$NGINX_CONF"
        echo -e "${GREEN}SSL证书配置完成${NC}"
    else
        echo -e "${RED}证书文件不存在，将使用HTTP配置${NC}"
        # 创建仅HTTP的配置
        cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # 日志配置
    access_log /var/log/nginx/website-monitor.access.log;
    error_log /var/log/nginx/website-monitor.error.log;

    # 主应用反向代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 隐藏敏感文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF
    fi
else
    echo -e "${BLUE}提示: 可以稍后使用Let's Encrypt获取免费SSL证书${NC}"
    echo "命令: certbot --nginx -d $DOMAIN"

    # 创建仅HTTP的配置
    cat > "$NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # 日志配置
    access_log /var/log/nginx/website-monitor.access.log;
    error_log /var/log/nginx/website-monitor.error.log;

    # 主应用反向代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # 超时配置
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 静态文件
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }

    # 隐藏敏感文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
EOF
fi

# 启用站点
if [ ! -L "$NGINX_ENABLED" ]; then
    ln -s "$NGINX_CONF" "$NGINX_ENABLED"
    echo -e "${GREEN}站点配置已启用${NC}"
fi

# 测试Nginx配置
echo -e "${YELLOW}测试Nginx配置...${NC}"
if nginx -t; then
    echo -e "${GREEN}Nginx配置测试通过${NC}"

    # 重载Nginx
    echo "重载Nginx配置..."
    systemctl reload nginx

    # 确保Nginx正在运行
    if ! systemctl is-active --quiet nginx; then
        echo "启动Nginx..."
        systemctl start nginx
        systemctl enable nginx
    fi

    echo -e "${GREEN}=== 配置完成 ===${NC}"
    echo
    echo -e "${BLUE}访问地址:${NC}"
    echo "http://$DOMAIN"
    if [[ $REPLY =~ ^[Yy]$ ]] && [ -f "$CERT_PATH" ] && [ -f "$KEY_PATH" ]; then
        echo "https://$DOMAIN"
    fi
    echo
    echo -e "${YELLOW}注意事项:${NC}"
    echo "1. 确保域名已解析到此服务器"
    echo "2. 确保网站监控服务正在运行: sudo systemctl status website-monitor"
    echo "3. 检查防火墙设置，开放80和443端口"
    echo "4. 如需SSL证书，可使用: certbot --nginx -d $DOMAIN"

else
    echo -e "${RED}Nginx配置测试失败，请检查配置文件${NC}"
    exit 1
fi