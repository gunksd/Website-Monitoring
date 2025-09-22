#!/bin/bash

# 网站监控系统启动脚本

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 网站监控系统启动脚本 ===${NC}"

# 检查Python版本
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Python版本: $PYTHON_VERSION"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}警告: 当前不在虚拟环境中${NC}"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 检查.env文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}未找到.env文件，正在从.env.example创建...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}请编辑.env文件配置必要的参数${NC}"
        echo "配置文件位置: $(pwd)/.env"
    else
        echo -e "${RED}错误: 未找到.env.example文件${NC}"
        exit 1
    fi
fi

# 安装依赖
echo "安装Python依赖..."
pip install -r requirements.txt

# 初始化数据库
echo "初始化数据库..."
python3 -c "
from app import create_app, db
app = create_app()
with app.app_context():
    db.create_all()
    print('数据库初始化完成')
"

# 检查端口
PORT=${PORT:-5000}
if netstat -tuln | grep -q ":$PORT "; then
    echo -e "${YELLOW}警告: 端口$PORT已被占用${NC}"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 启动应用
echo -e "${GREEN}启动网站监控系统...${NC}"
echo "访问地址: http://localhost:$PORT"
echo "按Ctrl+C停止服务"
echo

# 根据环境选择启动方式
if [[ "${FLASK_ENV}" == "production" ]]; then
    echo "生产环境模式，使用Gunicorn启动..."
    gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 --log-level info run:app
else
    echo "开发环境模式，使用Flask内置服务器..."
    python3 app.py
fi