import hashlib
import requests
import difflib
import json
from datetime import datetime
from bs4 import BeautifulSoup
from app import db
from app.models import Website, ChangeRecord, Keyword
from app.services.notification import NotificationService
from app.services.browser_fetcher import BrowserFetcher

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

    def is_dynamic_website(self, url):
        """判断是否为动态网站（简单规则）"""
        dynamic_patterns = [
            'javascript',
            'react',
            'next.js',
            'vue',
            'angular',
            'spa',
            'awansmith.cn'  # 已知的动态网站
        ]

        url_lower = url.lower()
        return any(pattern in url_lower for pattern in dynamic_patterns)

    def fetch_website_content_static(self, url, timeout=10):
        """获取静态网站内容（传统HTTP请求）"""
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

            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除脚本和样式标签
            for script in soup(["script", "style"]):
                script.decompose()

            # 获取纯文本内容
            text_content = soup.get_text()

            # 清理空白字符
            lines = (line.strip() for line in text_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            clean_text = ' '.join(chunk for chunk in chunks if chunk)

            # 获取标题和meta信息
            title = soup.find('title')
            title_text = title.get_text() if title else ""

            meta_content = []
            for meta in soup.find_all('meta', {'name': ['description', 'keywords', 'author']}):
                content = meta.get('content', '')
                if content:
                    meta_content.append(content)

            combined_content = f"{title_text} {clean_text} {' '.join(meta_content)}"
            return combined_content

        except Exception as e:
            print(f"Error fetching static content from {url}: {str(e)}")
            return None

    def fetch_website_content_dynamic(self, url):
        """获取动态网站内容（使用无头浏览器）"""
        try:
            browser_fetcher = BrowserFetcher()
            content = browser_fetcher.fetch_content_sync(url, wait_time=8000)
            return content

        except Exception as e:
            print(f"Error fetching dynamic content from {url}: {str(e)}")
            return None

    def fetch_website_content(self, url, timeout=10):
        """获取网站内容（自动选择静态或动态方法）"""
        print(f"Fetching content from: {url}")

        # 首先尝试判断是否为动态网站
        if self.is_dynamic_website(url):
            print(f"Detected dynamic website, using browser fetcher for: {url}")
            content = self.fetch_website_content_dynamic(url)

            # 如果浏览器方法失败，回退到静态方法
            if content is None:
                print(f"Browser fetch failed, falling back to static method for: {url}")
                content = self.fetch_website_content_static(url, timeout)
        else:
            print(f"Using static fetch method for: {url}")
            content = self.fetch_website_content_static(url, timeout)

        return content

    def calculate_content_hash(self, content):
        """计算内容哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def check_keywords_match(self, content, keywords):
        """检查内容中是否包含关键词"""
        matched_keywords = []
        content_lower = content.lower()

        for keyword in keywords:
            if keyword.keyword.lower() in content_lower:
                matched_keywords.append(keyword.keyword)

        return matched_keywords

    def generate_diff(self, old_content, new_content):
        """生成内容差异"""
        old_lines = old_content.splitlines() if old_content else []
        new_lines = new_content.splitlines() if new_content else []

        diff = list(difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='Previous Content',
            tofile='Current Content',
            lineterm=''
        ))

        return '\n'.join(diff)

    def generate_change_summary(self, old_content, new_content):
        """生成变化摘要"""
        if not old_content:
            return "首次抓取内容"

        old_lines = set(old_content.splitlines()) if old_content else set()
        new_lines = set(new_content.splitlines()) if new_content else set()

        added_lines = new_lines - old_lines
        removed_lines = old_lines - new_lines

        summary_parts = []

        if added_lines:
            # 获取最重要的新增内容（去除空行和过短的行）
            important_added = [line.strip() for line in added_lines
                             if line.strip() and len(line.strip()) > 10][:3]
            if important_added:
                summary_parts.append(f"新增: {'; '.join(important_added)}")

        if removed_lines:
            important_removed = [line.strip() for line in removed_lines
                               if line.strip() and len(line.strip()) > 10][:2]
            if important_removed:
                summary_parts.append(f"移除: {'; '.join(important_removed)}")

        if not summary_parts:
            return "检测到内容变化"

        summary = " | ".join(summary_parts)
        return summary[:200] + "..." if len(summary) > 200 else summary

    def monitor_website(self, website):
        """监控单个网站"""
        print(f"Checking website: {website.name} ({website.url})")

        # 获取当前内容
        current_content = self.fetch_website_content(website.url)
        if current_content is None:
            print(f"Failed to fetch content for {website.url}")
            return False

        # 计算当前内容哈希
        current_hash = self.calculate_content_hash(current_content)

        # 更新检查时间
        website.last_checked = datetime.utcnow()

        # 如果是第一次检查，直接保存哈希值
        if not website.last_content_hash:
            website.last_content_hash = current_hash
            db.session.commit()
            print(f"First check for {website.name}, saved content hash")
            return True

        # 检查内容是否有变化
        if current_hash != website.last_content_hash:
            print(f"Content changed for {website.name}")

            # 获取旧内容 - 从最近的变化记录中获取
            old_content = ""
            latest_record = ChangeRecord.query.filter_by(website_id=website.id)\
                                              .order_by(ChangeRecord.created_at.desc()).first()
            if latest_record:
                old_content = latest_record.content_after

            # 生成差异和变化摘要
            diff_content = self.generate_diff(old_content, current_content)
            change_summary = self.generate_change_summary(old_content, current_content)

            # 检查关键词匹配
            matched_keywords = self.check_keywords_match(current_content, website.keywords)

            # 创建变化记录
            change_record = ChangeRecord(
                website_id=website.id,
                change_type='keyword_matched' if matched_keywords else 'content_changed',
                content_after=current_content[:2000],  # 存储更多内容用于下次比较
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
                    self.notification_service.send_notification(
                        website, change_record, matched_keywords, change_summary
                    )
                    change_record.notification_sent = True
                    print(f"Notification sent for {website.name}")
                except Exception as e:
                    print(f"Failed to send notification: {str(e)}")
            else:
                print(f"Content changed for {website.name}, but no keywords matched")

            # 更新网站哈希值
            website.last_content_hash = current_hash

            db.session.commit()
            return True
        else:
            print(f"No changes detected for {website.name}")
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