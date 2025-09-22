#!/usr/bin/env python3
"""
网站监控系统主应用
"""

import os
import atexit
from app import create_app, db
from app.services.scheduler import MonitorScheduler

# 创建Flask应用
app = create_app()

# 创建调度器实例
scheduler = MonitorScheduler(app)

def init_database():
    """初始化数据库"""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully")

def start_monitoring():
    """启动监控调度器"""
    try:
        scheduler.start_monitoring()
        print("Website monitoring started")
    except Exception as e:
        print(f"Failed to start monitoring: {e}")

def stop_monitoring():
    """停止监控调度器"""
    try:
        scheduler.stop_monitoring()
        print("Website monitoring stopped")
    except Exception as e:
        print(f"Failed to stop monitoring: {e}")

# 注册退出时的清理函数
atexit.register(stop_monitoring)

if __name__ == '__main__':
    # 初始化数据库
    init_database()

    # 启动监控
    start_monitoring()

    # 运行Flask应用
    app.run(
        host=app.config.get('HOST', '0.0.0.0'),
        port=app.config.get('PORT', 5000),
        debug=app.config.get('DEBUG', False)
    )