#!/usr/bin/env python3
"""
快速测试监控功能 - 每30秒检查一次
"""

import time
from app import create_app, db
from app.models import Website
from app.services.monitor import WebsiteMonitor

def quick_test():
    """快速测试 - 每30秒运行一次监控"""
    app = create_app()

    print("🚀 开始快速监控测试...")
    print("📅 每30秒检查一次网站变化")
    print("🔄 运行3轮测试\n")

    monitor = WebsiteMonitor()

    for round_num in range(1, 4):
        print(f"{'='*60}")
        print(f"🔍 第 {round_num} 轮检查 - {time.strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        with app.app_context():
            websites = Website.query.filter_by(is_active=True).all()

            for i, website in enumerate(websites, 1):
                print(f"\n[{i}] 检查: {website.name} ({website.url})")

                try:
                    result = monitor.monitor_website(website)
                    if result:
                        print("✅ 检查完成")
                    else:
                        print("❌ 检查失败")
                except Exception as e:
                    print(f"💥 错误: {str(e)}")

        if round_num < 3:
            print(f"\n⏳ 等待30秒进行下一轮检查...")
            time.sleep(30)

    print(f"\n{'='*60}")
    print("🎉 快速测试完成!")

if __name__ == "__main__":
    quick_test()