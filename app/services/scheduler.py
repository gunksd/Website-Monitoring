from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.services.monitor import WebsiteMonitor
from flask import current_app

class MonitorScheduler:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.monitor = WebsiteMonitor()
        self.app = app

    def monitor_with_context(self):
        """在应用上下文中执行监控"""
        with self.app.app_context():
            self.monitor.monitor_all_websites()

    def start_monitoring(self):
        """启动监控任务"""
        # 添加定时任务，每5分钟执行一次
        self.scheduler.add_job(
            func=self.monitor_with_context,
            trigger=IntervalTrigger(minutes=5),
            id='website_monitoring',
            name='Website Content Monitoring',
            replace_existing=True
        )

        self.scheduler.start()
        print("Website monitoring scheduler started")

    def stop_monitoring(self):
        """停止监控任务"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Website monitoring scheduler stopped")

    def is_running(self):
        """检查调度器是否在运行"""
        return self.scheduler.running