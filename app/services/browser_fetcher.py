import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import os

class BrowserFetcher:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def start_browser(self):
        """启动浏览器"""
        try:
            self.playwright = await async_playwright().start()

            # 尝试启动Chromium
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )

            # 创建上下文
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            return True

        except Exception as e:
            print(f"Failed to start browser: {str(e)}")
            return False

    async def fetch_content(self, url, wait_time=5000):
        """获取动态网站内容"""
        if not self.context:
            if not await self.start_browser():
                return None

        try:
            page = await self.context.new_page()

            # 设置超时时间
            page.set_default_timeout(30000)

            # 访问页面
            await page.goto(url, wait_until='networkidle')

            # 等待页面加载完成
            await page.wait_for_timeout(wait_time)

            # 获取页面内容
            content = await page.content()

            # 关闭页面
            await page.close()

            # 解析内容
            soup = BeautifulSoup(content, 'html.parser')

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

            # 提取meta标签内容
            meta_content = []
            for meta in soup.find_all('meta', {'name': ['description', 'keywords', 'author']}):
                content_attr = meta.get('content', '')
                if content_attr:
                    meta_content.append(content_attr)

            # 合并所有内容
            combined_content = f"{title_text} {clean_text} {' '.join(meta_content)}"

            return combined_content

        except Exception as e:
            print(f"Error fetching content from {url}: {str(e)}")
            return None

    async def close_browser(self):
        """关闭浏览器"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            print(f"Error closing browser: {str(e)}")

    def fetch_content_sync(self, url, wait_time=5000):
        """同步版本的内容获取"""
        async def fetch_with_new_browser():
            # 为每个请求创建新的浏览器实例
            browser_fetcher = BrowserFetcher()
            try:
                content = await browser_fetcher.fetch_content(url, wait_time)
                return content
            finally:
                await browser_fetcher.close_browser()

        try:
            # 创建新的事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                return loop.run_until_complete(fetch_with_new_browser())
            finally:
                loop.close()

        except Exception as e:
            print(f"Error in sync fetch: {str(e)}")
            return None