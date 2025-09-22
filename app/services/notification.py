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
            # 转换为中国时区时间
            if change_record.created_at:
                # 假设数据库中存储的是UTC时间，转换为北京时间
                china_tz = timezone(timedelta(hours=8))
                beijing_time = change_record.created_at.replace(tzinfo=timezone.utc).astimezone(china_tz)
                created_time = beijing_time.strftime('%Y-%m-%d %H:%M:%S')
            else:
                # 如果没有时间，使用当前北京时间
                china_tz = timezone(timedelta(hours=8))
                current_time = datetime.now(china_tz)
                created_time = current_time.strftime('%Y-%m-%d %H:%M:%S')

            content = f"网站监控告警\n\n网站: {website.name}\nURL: {website.url}\n时间: {created_time} (北京时间)"

            if matched_keywords:
                content += f"\n关键词: {', '.join(matched_keywords)}"
            else:
                content += f"\n监控: 全量监控"

            if change_summary:
                content += f"\n摘要: {change_summary}"

            payload = {
                "msgtype": "text",
                "text": {
                    "content": content
                }
            }

            print(f"Sending webhook to: {self.config.WEBHOOK_URL}")
            print(f"Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            response = requests.post(
                self.config.WEBHOOK_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )

            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

            response.raise_for_status()

            # 检查企业微信返回的错误码
            try:
                resp_data = response.json()
                if resp_data.get('errcode', 0) != 0:
                    print(f"WeChat API error: {resp_data}")
                    return False
                else:
                    print(f"WeChat Work webhook notification sent successfully for {website.name}")
                    return True
            except json.JSONDecodeError:
                print(f"WeChat Work webhook notification sent for {website.name} (non-JSON response)")
                return True

        except Exception as e:
            print(f"Failed to send webhook notification: {str(e)}")
            return False

    def send_notification(self, website, change_record, matched_keywords, change_summary=None):
        """发送通知（仅Webhook）"""
        return self.send_webhook_notification(website, change_record, matched_keywords, change_summary)