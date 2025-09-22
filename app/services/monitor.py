import hashlib
import requests
import difflib
import json
from datetime import datetime
from bs4 import BeautifulSoup
from app import db
from app.models import Website, ChangeRecord, Keyword
from app.services.notification import NotificationService

class WebsiteMonitor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.notification_service = NotificationService()

    def fetch_website_content(self, url, timeout=15):
        """获取网站HTML内容"""
        print(f"Fetching HTML content from: {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            }

            response = self.session.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()

            return response.text

        except Exception as e:
            print(f"Error fetching content from {url}: {str(e)}")
            return None

    def calculate_content_hash(self, content):
        """计算内容哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def check_keywords_match(self, html_content, keywords):
        """检查HTML内容中是否包含关键词"""
        matched_keywords = []
        html_lower = html_content.lower()

        for keyword in keywords:
            if keyword.keyword.lower() in html_lower:
                matched_keywords.append(keyword.keyword)

        return matched_keywords

    def generate_diff(self, old_html, new_html):
        """生成HTML差异"""
        if not old_html:
            return "首次检测"

        old_lines = old_html.splitlines()
        new_lines = new_html.splitlines()

        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='Previous HTML',
            tofile='Current HTML',
            lineterm='',
            n=3
        ))

        return '\n'.join(diff[:50])

    def generate_change_summary(self, old_html, new_html):
        """生成HTML变化摘要"""
        if not old_html:
            return "首次抓取HTML"

        old_length = len(old_html)
        new_length = len(new_html)

        if new_length > old_length:
            return f"HTML增加了 {new_length - old_length} 个字符"
        elif new_length < old_length:
            return f"HTML减少了 {old_length - new_length} 个字符"
        else:
            return "HTML内容发生变化"

    def monitor_website(self, website):
        """监控单个网站的HTML变化"""
        print(f"Checking website: {website.name} ({website.url})")

        # 获取当前HTML内容
        current_html = self.fetch_website_content(website.url)
        if current_html is None:
            print(f"Failed to fetch HTML content for {website.url}")
            return False

        # 计算当前HTML哈希
        current_hash = self.calculate_content_hash(current_html)

        # 更新检查时间
        website.last_checked = datetime.utcnow()

        # 如果是第一次检查，直接保存哈希值
        if not website.last_content_hash:
            website.last_content_hash = current_hash
            db.session.commit()
            print(f"First check for {website.name}, saved HTML hash")
            return True

        # 检查HTML是否有变化
        if current_hash != website.last_content_hash:
            print(f"HTML content changed for {website.name}")

            # 获取旧HTML - 从最近的变化记录中获取
            old_html = ""
            latest_record = ChangeRecord.query.filter_by(website_id=website.id)\
                                              .order_by(ChangeRecord.created_at.desc()).first()
            if latest_record:
                old_html = latest_record.content_after

            # 生成差异和变化摘要
            diff_content = self.generate_diff(old_html, current_html)
            change_summary = self.generate_change_summary(old_html, current_html)

            # 检查关键词匹配
            matched_keywords = self.check_keywords_match(current_html, website.keywords)

            # 创建变化记录
            change_record = ChangeRecord(
                website_id=website.id,
                change_type='keyword_matched' if matched_keywords else 'html_changed',
                content_after=current_html[:5000],  # 存储更多HTML用于下次比较
                diff_content=diff_content,
                matched_keywords=json.dumps(matched_keywords) if matched_keywords else None
            )

            db.session.add(change_record)

            # 发送通知逻辑：
            # 1. 如果没有设置关键词，所有变化都通知
            # 2. 如果设置了关键词，只有匹配时才通知
            should_notify = False
            if not website.keywords:  # 没有设置关键词，所有变化都通知
                should_notify = True
                matched_keywords = []  # 空列表表示没有关键词过滤
            elif matched_keywords:  # 有关键词且匹配，发送通知
                should_notify = True

            if should_notify:
                try:
                    print(f"Sending notification for {website.name}...")
                    success = self.notification_service.send_notification(
                        website, change_record, matched_keywords, change_summary
                    )
                    change_record.notification_sent = success
                    if success:
                        print(f"Notification sent successfully for {website.name}")
                    else:
                        print(f"Notification failed for {website.name}")
                except Exception as e:
                    print(f"Failed to send notification for {website.name}: {str(e)}")
            else:
                print(f"HTML changed for {website.name}, but no keywords matched")

            # 更新网站哈希值
            website.last_content_hash = current_hash

            db.session.commit()
            return True
        else:
            print(f"No HTML changes detected for {website.name}")
            db.session.commit()
            return True

    def monitor_all_websites(self):
        """监控所有活跃的网站"""
        active_websites = Website.query.filter_by(is_active=True).all()

        print(f"Starting monitoring of {len(active_websites)} websites")

        for website in active_websites:
            try:
                self.monitor_website(website)
            except Exception as e:
                print(f"Error monitoring {website.name}: {str(e)}")

        print("Monitoring cycle completed")