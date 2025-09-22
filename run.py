#!/usr/bin/env python3
"""
网站监控系统生产环境启动脚本
使用Gunicorn运行
"""

import os
import sys
from app import create_app, db
from app.services.scheduler import MonitorScheduler

# 创建Flask应用
app = create_app()

# 全局调度器实例
scheduler = None

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

def init_scheduler():
    """初始化并启动调度器"""
    global scheduler
    try:
        scheduler = MonitorScheduler()
        scheduler.start_monitoring()
        print("Website monitoring scheduler started")
    except Exception as e:
        print(f"Failed to start monitoring scheduler: {e}")

# 初始化数据库
init_database()

# 在worker进程中启动调度器
if __name__ != '__main__':
    init_scheduler()

if __name__ == '__main__':
    # 开发模式直接运行
    init_scheduler()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )