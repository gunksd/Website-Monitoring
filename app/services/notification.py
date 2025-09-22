import requests
import json
from datetime import datetime, timezone, timedelta
from config.config import Config

class NotificationService:
    def __init__(self):
        self.config = Config()

    def send_webhook_notification(self, website, change_record, matched_keywords, change_summary=None):
        """发送企业微信Webhook通知"""
        if not self.config.WEBHOOK_URL:
            print("Webhook URL not configured, skipping webhook notification")
            return False

        try:
            # 使用当前北京时间
            china_tz = timezone(timedelta(hours=8))
            current_time = datetime.now(china_tz)
            created_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

            # 构建通知内容
            content = f"🚨 网站监控告警\n\n📍 网站: {website.name}\n🌐 URL: {website.url}\n⏰ 时间: {created_time}"

            if matched_keywords:
                content += f"\n🔑 关键词匹配: {', '.join(matched_keywords)}"
            else:
                content += f"\n📊 监控类型: HTML全量监控"

            if change_summary:
                content += f"\n📝 变化摘要: {change_summary}"

            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            print(f"[WEBHOOK] Sending to: {self.config.WEBHOOK_URL}")
            print(f"[WEBHOOK] Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            # 发送请求，增加重试机制
            max_retries = 3
            for retry in range(max_retries):
                try:
                    response = requests.post(
                        self.config.WEBHOOK_URL,
                        json=payload,
                        headers={
                            'Content-Type': 'application/json',
                            'User-Agent': 'Website-Monitor/1.0'
                        },
                        timeout=15
                    )

                    print(f"[WEBHOOK] Response status: {response.status_code}")
                    print(f"[WEBHOOK] Response body: {response.text}")

                    if response.status_code == 200:
                        # 检查企业微信返回的错误码
                        try:
                            resp_data = response.json()
                            if resp_data.get('errcode', 0) == 0:
                                print(f"[WEBHOOK] ✅ Notification sent successfully for {website.name}")
                                return True
                            else:
                                print(f"[WEBHOOK] ❌ WeChat API error: {resp_data}")
                                if retry < max_retries - 1:
                                    print(f"[WEBHOOK] Retrying... ({retry + 1}/{max_retries})")
                                    continue
                                return False
                        except json.JSONDecodeError:
                            print(f"[WEBHOOK] ✅ Notification sent for {website.name} (non-JSON response)")
                            return True
                    else:
                        if retry < max_retries - 1:
                            print(f"[WEBHOOK] HTTP {response.status_code}, retrying... ({retry + 1}/{max_retries})")
                            continue
                        response.raise_for_status()

                except requests.exceptions.Timeout:
                    print(f"[WEBHOOK] ⏰ Timeout error, retry {retry + 1}/{max_retries}")
                    if retry == max_retries - 1:
                        raise
                except requests.exceptions.ConnectionError:
                    print(f"[WEBHOOK] 🔌 Connection error, retry {retry + 1}/{max_retries}")
                    if retry == max_retries - 1:
                        raise

            return False

        except Exception as e:
            print(f"[WEBHOOK] ❌ Failed to send notification: {str(e)}")
            import traceback
            print(f"[WEBHOOK] Error details: {traceback.format_exc()}")
            return False

    def send_notification(self, website, change_record, matched_keywords, change_summary=None):
        """发送通知（仅Webhook）"""
        return self.send_webhook_notification(website, change_record, matched_keywords, change_summary)