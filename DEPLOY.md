# 阿里云ECS部署详细指南

本文档提供在阿里云ECS服务器上部署网站监控系统的详细步骤。

## 🚀 部署前准备

### 1. 阿里云ECS配置要求

#### 推荐配置
- **CPU**: 2核
- **内存**: 2GB
- **存储**: 20GB SSD
- **带宽**: 1Mbps（可根据需求调整）
- **操作系统**: Ubuntu 20.04 LTS / CentOS 8

#### 最低配置
- **CPU**: 1核
- **内存**: 1GB
- **存储**: 10GB
- **带宽**: 1Mbps

### 2. 购买ECS实例

1. 登录阿里云控制台
2. 选择"云服务器ECS" -> "实例"
3. 点击"创建实例"
4. 选择合适的配置
5. 配置安全组，开放必要端口

### 3. 安全组配置

在ECS控制台的安全组中添加以下规则：

| 端口范围 | 授权对象 | 描述 |
|---------|---------|-----|
| 22/22 | 0.0.0.0/0 | SSH连接 |
| 80/80 | 0.0.0.0/0 | HTTP访问 |
| 443/443 | 0.0.0.0/0 | HTTPS访问 |
| 5000/5000 | 127.0.0.1/32 | 应用端口（仅本地） |

## 📋 详细部署步骤

### 第一步：连接服务器

使用SSH连接到ECS实例：

```bash
# 使用密码连接
ssh root@your-server-ip

# 使用密钥连接
ssh -i /path/to/your-key.pem root@your-server-ip
```

### 第二步：系统初始化

```bash
# 更新系统
apt update && apt upgrade -y  # Ubuntu/Debian
# 或
yum update -y  # CentOS/RHEL

# 安装基础工具
apt install -y curl wget git vim net-tools  # Ubuntu/Debian
# 或
yum install -y curl wget git vim net-tools  # CentOS/RHEL

# 设置时区
timedatectl set-timezone Asia/Shanghai

# 创建专用用户
useradd -m -s /bin/bash monitor
usermod -aG sudo monitor
passwd monitor  # 设置密码

# 配置SSH密钥（推荐）
mkdir -p /home/monitor/.ssh
cp ~/.ssh/authorized_keys /home/monitor/.ssh/
chown -R monitor:monitor /home/monitor/.ssh
chmod 700 /home/monitor/.ssh
chmod 600 /home/monitor/.ssh/authorized_keys
```

### 第三步：安装Python环境

```bash
# 切换到monitor用户
su - monitor

# 安装Python 3.10+
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 验证Python版本
python3 --version  # 应该是3.10+

# 如果版本过低，安装更新的Python
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev
```

### 第四步：下载和安装项目

```bash
# 方法1：从Git仓库下载
git clone https://github.com/your-username/website-monitoring.git /opt/website-monitor

# 方法2：上传项目文件
# 在本地使用scp上传
# scp -r website-monitoring/ monitor@your-server-ip:/opt/

# 设置目录权限
sudo chown -R monitor:monitor /opt/website-monitor
cd /opt/website-monitor
```

### 第五步：运行安装脚本

```bash
# 给脚本执行权限
chmod +x install.sh

# 运行安装脚本
sudo ./install.sh
```

安装脚本会自动：
- 创建Python虚拟环境
- 安装所需依赖
- 初始化数据库
- 创建systemd服务
- 启动应用服务

### 第六步：配置应用

```bash
# 编辑配置文件
nano /opt/website-monitor/.env
```

关键配置项：

```bash
# 生成一个安全的SECRET_KEY
SECRET_KEY=your-very-secure-secret-key-here

# 数据库路径
DATABASE_URL=sqlite:///website_monitor.db

# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Webhook配置
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK

# 生产环境配置
FLASK_ENV=production
DEBUG=False
```

### 第七步：配置Nginx

```bash
# 进入nginx目录
cd /opt/website-monitor/nginx

# 运行nginx配置脚本
sudo ./nginx-setup.sh
```

脚本会询问：
1. 域名：输入您的域名（如 example.com）
2. SSL证书：如果已有证书，提供证书路径

### 第八步：域名解析配置

在您的域名注册商管理面板中：

1. 添加A记录：`@ -> 您的ECS公网IP`
2. 添加A记录：`www -> 您的ECS公网IP`

等待DNS解析生效（通常5-30分钟）。

### 第九步：申请SSL证书（推荐）

使用Let's Encrypt免费SSL证书：

```bash
# 安装certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 设置自动续期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 第十步：验证部署

```bash
# 检查服务状态
sudo systemctl status website-monitor

# 检查Nginx状态
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep -E ':(80|443|5000)'

# 测试网站访问
curl -I http://your-domain.com
curl -I https://your-domain.com
```

## 🔧 高级配置

### 1. 性能优化

#### Gunicorn配置优化

编辑 `/etc/systemd/system/website-monitor.service`：

```ini
[Service]
# 调整worker数量（CPU核数 x 2 + 1）
ExecStart=/opt/website-monitor/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 --timeout 120 --max-requests 1000 --max-requests-jitter 50 run:app
```

#### Nginx配置优化

编辑 `/etc/nginx/sites-available/website-monitor`：

```nginx
# 在http块中添加
client_max_body_size 10m;
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;

# 启用缓存
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=website_monitor:10m max_size=1g inactive=60m use_temp_path=off;

# 在location /中添加
proxy_cache website_monitor;
proxy_cache_valid 200 5m;
```

### 2. 数据库优化

```bash
# 创建数据备份脚本
cat > /opt/website-monitor/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/website-monitor/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/website-monitor/website_monitor.db $BACKUP_DIR/website_monitor_$DATE.db

# 保留最近30天的备份
find $BACKUP_DIR -name "website_monitor_*.db" -mtime +30 -delete

echo "Backup completed: website_monitor_$DATE.db"
EOF

chmod +x /opt/website-monitor/backup.sh

# 设置定时备份
crontab -e
# 添加：每天凌晨2点备份
# 0 2 * * * /opt/website-monitor/backup.sh
```

### 3. 监控和日志

#### 系统监控脚本

```bash
cat > /opt/website-monitor/monitor.sh << 'EOF'
#!/bin/bash

# 检查服务状态
if ! systemctl is-active --quiet website-monitor; then
    echo "$(date): Website monitor service is down!" >> /var/log/website-monitor-health.log
    systemctl restart website-monitor
fi

# 检查磁盘空间
DISK_USAGE=$(df /opt/website-monitor | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "$(date): Disk usage is high: ${DISK_USAGE}%" >> /var/log/website-monitor-health.log
fi

# 检查内存使用
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "$(date): Memory usage is high: ${MEM_USAGE}%" >> /var/log/website-monitor-health.log
fi
EOF

chmod +x /opt/website-monitor/monitor.sh

# 设置定时检查
crontab -e
# 添加：每10分钟检查一次
# */10 * * * * /opt/website-monitor/monitor.sh
```

#### 日志轮转配置

```bash
sudo tee /etc/logrotate.d/website-monitor << 'EOF'
/var/log/nginx/website-monitor.*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}

/var/log/website-monitor-health.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 monitor monitor
}
EOF
```

### 4. 安全加固

#### 防火墙配置

```bash
# 使用ufw（Ubuntu）
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# 使用firewall-cmd（CentOS）
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### SSH安全配置

```bash
sudo nano /etc/ssh/sshd_config

# 修改以下配置
Port 22022  # 更改默认端口
PermitRootLogin no  # 禁止root登录
PasswordAuthentication no  # 仅允许密钥认证
AllowUsers monitor  # 仅允许指定用户

sudo systemctl restart sshd

# 更新防火墙规则
sudo ufw allow 22022/tcp
sudo ufw delete allow ssh
```

#### Nginx安全头配置

在nginx配置中添加安全头：

```nginx
add_header X-Frame-Options DENY always;
add_header X-Content-Type-Options nosniff always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

### 5. 故障恢复

#### 自动恢复脚本

```bash
cat > /opt/website-monitor/recovery.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/website-monitor-recovery.log"

log_message() {
    echo "$(date): $1" >> $LOG_FILE
}

# 检查并恢复website-monitor服务
if ! systemctl is-active --quiet website-monitor; then
    log_message "Website monitor service is down, attempting recovery..."
    systemctl restart website-monitor
    sleep 10

    if systemctl is-active --quiet website-monitor; then
        log_message "Website monitor service recovered successfully"
    else
        log_message "Failed to recover website monitor service"
    fi
fi

# 检查并恢复nginx服务
if ! systemctl is-active --quiet nginx; then
    log_message "Nginx service is down, attempting recovery..."
    systemctl restart nginx
    sleep 5

    if systemctl is-active --quiet nginx; then
        log_message "Nginx service recovered successfully"
    else
        log_message "Failed to recover nginx service"
    fi
fi

# 检查磁盘空间，清理日志
DISK_USAGE=$(df /opt/website-monitor | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    log_message "Disk usage critical: ${DISK_USAGE}%, cleaning up logs..."
    find /var/log -name "*.log" -mtime +7 -exec rm -f {} \;
    find /opt/website-monitor/backups -name "*.db" -mtime +7 -delete
fi
EOF

chmod +x /opt/website-monitor/recovery.sh

# 设置定时执行
crontab -e
# 添加：每5分钟检查一次
# */5 * * * * /opt/website-monitor/recovery.sh
```

## 📊 部署验证清单

部署完成后，请逐项验证：

### 基础验证
- [ ] 服务器可通过SSH连接
- [ ] Python 3.10+正确安装
- [ ] 项目文件正确上传
- [ ] 虚拟环境创建成功
- [ ] 依赖包安装完成

### 应用验证
- [ ] 数据库初始化成功
- [ ] 配置文件正确设置
- [ ] website-monitor服务运行正常
- [ ] 本地5000端口可访问

### Web服务验证
- [ ] Nginx安装并运行
- [ ] 域名正确解析到服务器IP
- [ ] HTTP访问正常
- [ ] HTTPS证书配置成功
- [ ] SSL证书自动续期配置

### 功能验证
- [ ] 可以添加监控网站
- [ ] 网站检测功能正常
- [ ] 邮件通知发送成功
- [ ] Webhook通知正常
- [ ] 变化记录正确显示

### 安全验证
- [ ] 防火墙规则正确配置
- [ ] SSH安全配置生效
- [ ] SSL证书有效
- [ ] 安全头正确设置

### 运维验证
- [ ] 自动启动配置正常
- [ ] 日志记录正常
- [ ] 备份脚本运行正常
- [ ] 监控脚本配置成功

## 🎯 性能调优建议

### 1. 监控频率优化
- 根据网站重要性调整检查间隔
- 重要网站：5-10分钟
- 一般网站：30-60分钟
- 不重要网站：2-6小时

### 2. 资源使用优化
```bash
# 限制Python进程内存使用
echo 'vm.overcommit_memory = 1' >> /etc/sysctl.conf
echo 'vm.max_map_count = 262144' >> /etc/sysctl.conf
sysctl -p
```

### 3. 网络优化
```bash
# 优化TCP连接
echo 'net.core.somaxconn = 1024' >> /etc/sysctl.conf
echo 'net.ipv4.tcp_max_syn_backlog = 2048' >> /etc/sysctl.conf
sysctl -p
```

完成以上所有步骤后，您的网站监控系统就已经成功部署在阿里云ECS上了！