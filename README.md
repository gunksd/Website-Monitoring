# 网站监控系统

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

一个功能完整的网站内容变化监控系统，支持关键词过滤、实时通知和直观的Web管理界面。

![系统架构图](docs/architecture.png)

## 🚀 功能特性

### 核心功能
- ✅ **网站内容监控**: 定时抓取网站页面内容，检测变化
- 🔍 **智能关键词过滤**: 只有包含指定关键词的变化才触发通知
- 📧 **多种通知方式**: 支持邮件和Webhook通知
- 🌐 **直观Web界面**: Bootstrap风格的管理界面
- 📱 **响应式设计**: 完美支持移动设备
- 🔐 **安全可靠**: HTTPS支持，数据加密存储

### 技术特性
- 🐍 Python 3.10+ + Flask框架
- 🗄️ SQLite轻量级数据库
- ⚡ APScheduler定时任务调度
- 🔄 异步监控处理
- 📊 完整的变化历史记录
- 🎯 RESTful API接口

## 📋 系统要求

- **操作系统**: Ubuntu 18.04+ / CentOS 7+ / Debian 10+
- **Python**: 3.10或更高版本
- **内存**: 至少512MB RAM
- **存储**: 至少1GB可用空间
- **网络**: 可访问互联网

## 🛠️ 快速安装

### 方式一：一键安装脚本（推荐）

```bash
# 下载项目
git clone https://github.com/your-username/website-monitoring.git
cd website-monitoring

# 运行安装脚本
sudo ./install.sh
```

### 方式二：手动安装

1. **克隆项目**
```bash
git clone https://github.com/your-username/website-monitoring.git
cd website-monitoring
```

2. **创建Python虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
nano .env  # 编辑配置文件
```

5. **初始化数据库**
```bash
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **启动应用**
```bash
./start.sh
```

## ⚙️ 配置说明

编辑 `.env` 文件配置系统参数：

```bash
# Flask配置
SECRET_KEY=your-secret-key-here
DEBUG=False

# 数据库配置
DATABASE_URL=sqlite:///website_monitor.db

# 邮件配置（Gmail示例）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Webhook配置（Slack示例）
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 应用配置
HOST=0.0.0.0
PORT=5000
```

### 邮件配置说明

#### Gmail配置
1. 启用两步验证
2. 生成应用专用密码
3. 使用应用专用密码作为 `EMAIL_PASSWORD`

#### 其他邮箱配置
```bash
# Outlook
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587

# QQ邮箱
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587

# 163邮箱
SMTP_SERVER=smtp.163.com
SMTP_PORT=25
```

## 🌐 Nginx配置

### 自动配置（推荐）
```bash
cd nginx
sudo ./nginx-setup.sh
```

### 手动配置
1. **复制配置文件**
```bash
sudo cp nginx/website-monitor.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/website-monitor /etc/nginx/sites-enabled/
```

2. **修改域名**
```bash
sudo nano /etc/nginx/sites-available/website-monitor
# 替换 your-domain.com 为实际域名
```

3. **测试并重载配置**
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### SSL证书配置

#### 使用Let's Encrypt（免费）
```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com
```

#### 使用自有证书
修改nginx配置文件中的证书路径：
```nginx
ssl_certificate /path/to/your/certificate.crt;
ssl_certificate_key /path/to/your/private.key;
```

## 🚀 阿里云ECS部署指南

### 1. 购买和配置ECS实例

1. **选择配置**
   - CPU: 1核或2核
   - 内存: 2GB或更高
   - 系统盘: 20GB SSD
   - 网络: 按需选择带宽

2. **安全组配置**
   - 开放端口: 22(SSH), 80(HTTP), 443(HTTPS)

### 2. 连接服务器

```bash
ssh root@your-server-ip
```

### 3. 创建专用用户

```bash
# 创建用户
useradd -m -s /bin/bash monitor
usermod -aG sudo monitor

# 切换用户
su - monitor
```

### 4. 部署应用

```bash
# 上传项目文件（使用scp、git等方式）
git clone https://github.com/your-username/website-monitoring.git
cd website-monitoring

# 运行安装脚本
sudo ./install.sh
```

### 5. 配置域名解析

在域名注册商处添加A记录：
```
@ -> your-server-ip
www -> your-server-ip
```

### 6. 配置Nginx和SSL

```bash
cd nginx
sudo ./nginx-setup.sh
```

### 7. 防火墙配置

```bash
# Ubuntu/Debian
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## 📖 使用指南

### 1. 访问Web界面

打开浏览器访问：`http://your-domain.com` 或 `https://your-domain.com`

### 2. 添加监控网站

1. 点击"添加网站"按钮
2. 填写网站名称和URL
3. 设置检查间隔（建议5-30分钟）
4. 添加关键词过滤（可选）
5. 点击"添加网站"

### 3. 查看监控结果

- **首页**: 查看所有网站监控状态
- **网站详情**: 查看单个网站的变化记录
- **变化记录**: 查看系统所有变化记录

### 4. API使用

系统提供RESTful API接口：

```bash
# 获取所有网站
curl -X GET http://your-domain.com/api/websites

# 添加网站
curl -X POST http://your-domain.com/api/websites \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例网站",
    "url": "https://example.com",
    "keywords": ["更新", "发布"]
  }'

# 手动检查网站
curl -X POST http://your-domain.com/api/websites/1/check

# 获取变化记录
curl -X GET http://your-domain.com/api/changes
```

## 🔧 运维管理

### 服务管理

```bash
# 查看服务状态
sudo systemctl status website-monitor

# 启动/停止/重启服务
sudo systemctl start website-monitor
sudo systemctl stop website-monitor
sudo systemctl restart website-monitor

# 查看日志
sudo journalctl -u website-monitor -f

# 开机自启
sudo systemctl enable website-monitor
```

### 手动运维

```bash
# 启动应用
./start.sh

# 停止应用
./stop.sh

# 查看进程
ps aux | grep python
```

### 数据备份

```bash
# 备份数据库
cp website_monitor.db website_monitor.db.backup

# 备份配置文件
cp .env .env.backup

# 定时备份脚本
echo "0 2 * * * cp /opt/website-monitor/website_monitor.db /opt/website-monitor/backups/\$(date +\\%Y\\%m\\%d)_website_monitor.db" | crontab -
```

### 性能优化

1. **监控间隔优化**: 根据实际需求调整检查间隔
2. **关键词优化**: 使用精确的关键词减少误报
3. **日志管理**: 定期清理日志文件
4. **数据库优化**: 定期清理过期数据

```python
# 清理30天前的变化记录
from app import create_app, db
from app.models import ChangeRecord
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    old_records = ChangeRecord.query.filter(ChangeRecord.created_at < cutoff_date).all()
    for record in old_records:
        db.session.delete(record)
    db.session.commit()
    print(f"删除了 {len(old_records)} 条过期记录")
```

## 🐛 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查日志
sudo journalctl -u website-monitor -n 50

# 检查端口占用
sudo netstat -tlnp | grep :5000

# 检查Python环境
source /opt/website-monitor/venv/bin/activate
python -c "from app import create_app; print('OK')"
```

#### 2. 网站检测失败
- 检查网络连接
- 验证URL格式
- 检查目标网站是否可访问
- 查看用户代理是否被封禁

#### 3. 邮件发送失败
- 检查SMTP配置
- 验证邮箱密码
- 检查防火墙设置
- 确认邮箱服务商设置

#### 4. Nginx配置问题
```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 检查端口监听
sudo netstat -tlnp | grep nginx
```

### 调试模式

开启调试模式进行问题排查：

```bash
# 临时开启调试
export FLASK_ENV=development
export DEBUG=True
python3 app.py
```

## 📁 项目结构

```
website-monitoring/
├── app/                    # 应用主目录
│   ├── __init__.py        # Flask应用初始化
│   ├── models/            # 数据模型
│   │   ├── website.py     # 网站模型
│   │   ├── change_record.py # 变化记录模型
│   │   └── keyword.py     # 关键词模型
│   ├── routes/            # 路由处理
│   │   ├── web_routes.py  # Web页面路由
│   │   └── api_routes.py  # API路由
│   ├── services/          # 业务服务
│   │   ├── monitor.py     # 监控服务
│   │   ├── notification.py # 通知服务
│   │   └── scheduler.py   # 调度服务
│   ├── templates/         # HTML模板
│   │   ├── base.html      # 基础模板
│   │   ├── index.html     # 首页
│   │   ├── add_website.html # 添加网站
│   │   ├── edit_website.html # 编辑网站
│   │   ├── website_detail.html # 网站详情
│   │   └── changes_list.html # 变化记录
│   └── static/            # 静态文件
│       ├── css/style.css  # 样式文件
│       └── js/main.js     # JavaScript
├── config/                # 配置文件
│   └── config.py         # 应用配置
├── nginx/                 # Nginx配置
│   ├── website-monitor.conf # 站点配置
│   └── nginx-setup.sh    # 配置脚本
├── app.py                # 应用入口
├── run.py                # 生产环境入口
├── requirements.txt      # 依赖列表
├── .env.example         # 配置模板
├── start.sh             # 启动脚本
├── stop.sh              # 停止脚本
├── install.sh           # 安装脚本
└── README.md            # 说明文档
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📜 开源协议

本项目采用 [MIT](LICENSE) 协议开源。

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [Bootstrap](https://getbootstrap.com/) - CSS框架
- [APScheduler](https://apscheduler.readthedocs.io/) - Python任务调度
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML解析

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: support@example.com
- 🐛 Issue: [GitHub Issues](https://github.com/your-username/website-monitoring/issues)

---

**⭐ 如果这个项目对您有帮助，请给个Star支持一下！**