#!/bin/bash

# 网站监控系统安装脚本 - 适用于阿里云ECS

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [[ $EUID -eq 0 ]]; then
    echo -e "${RED}请不要以root用户身份运行此脚本${NC}"
    echo "建议创建专用用户: sudo useradd -m -s /bin/bash monitor"
    exit 1
fi

echo -e "${GREEN}=== 网站监控系统安装脚本 ===${NC}"
echo -e "${BLUE}适用于阿里云ECS Ubuntu/CentOS系统${NC}"
echo

# 检测系统类型
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
else
    echo -e "${RED}无法检测系统类型${NC}"
    exit 1
fi

echo "检测到系统: $OS $VER"

# 更新系统包
echo -e "${YELLOW}更新系统包...${NC}"
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt update && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip python3-venv git nginx
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip python3-venv git nginx
else
    echo -e "${RED}不支持的操作系统: $OS${NC}"
    exit 1
fi

# 安装项目
INSTALL_DIR="/opt/website-monitor"
echo -e "${YELLOW}安装位置: $INSTALL_DIR${NC}"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}目录已存在，正在备份...${NC}"
    sudo mv "$INSTALL_DIR" "${INSTALL_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# 复制文件
echo "复制项目文件..."
sudo mkdir -p "$INSTALL_DIR"
sudo cp -r . "$INSTALL_DIR/"
sudo chown -R $(whoami):$(whoami) "$INSTALL_DIR"

cd "$INSTALL_DIR"

# 创建Python虚拟环境
echo -e "${YELLOW}创建Python虚拟环境...${NC}"
python3 -m venv venv
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装依赖
echo "安装Python依赖包..."
pip install -r requirements.txt

# 安装Playwright浏览器
echo -e "${YELLOW}安装Playwright浏览器...${NC}"
playwright install chromium

# 安装Playwright系统依赖
echo "安装Playwright系统依赖..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt install -y libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libasound2
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]]; then
    sudo yum install -y nss atk at-spi2-atk libdrm libxkbcommon libxcomposite libxdamage libxrandr mesa-libgbm libXScrnSaver alsa-lib
fi

# 配置文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}创建配置文件...${NC}"
    cp .env.example .env

    # 生成随机SECRET_KEY
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    sed -i "s/your-secret-key-here/$SECRET_KEY/" .env

    echo -e "${YELLOW}请编辑配置文件: $INSTALL_DIR/.env${NC}"
    echo "配置邮件和Webhook等参数"
fi

# 初始化数据库
echo "初始化数据库..."
python3 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
"

# 创建systemd服务
echo -e "${YELLOW}创建系统服务...${NC}"
sudo tee /etc/systemd/system/website-monitor.service > /dev/null <<EOF
[Unit]
Description=Website Monitor System
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 2 -b 127.0.0.1:5000 --timeout 120 run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable website-monitor
sudo systemctl start website-monitor

# 检查服务状态
sleep 3
if sudo systemctl is-active --quiet website-monitor; then
    echo -e "${GREEN}✓ 网站监控服务启动成功${NC}"
else
    echo -e "${RED}✗ 服务启动失败，请查看日志: sudo journalctl -u website-monitor${NC}"
fi

# Nginx配置提示
echo
echo -e "${GREEN}=== 安装完成 ===${NC}"
echo
echo -e "${YELLOW}下一步操作:${NC}"
echo "1. 编辑配置文件: $INSTALL_DIR/.env"
echo "2. 配置Nginx反向代理"
echo "3. 申请SSL证书"
echo "4. 配置防火墙规则"
echo
echo -e "${BLUE}服务管理命令:${NC}"
echo "启动服务: sudo systemctl start website-monitor"
echo "停止服务: sudo systemctl stop website-monitor"
echo "重启服务: sudo systemctl restart website-monitor"
echo "查看状态: sudo systemctl status website-monitor"
echo "查看日志: sudo journalctl -u website-monitor -f"
echo
echo -e "${BLUE}访问地址:${NC}"
echo "本地访问: http://localhost:5000"
echo "配置Nginx后可通过域名访问"

deactivate