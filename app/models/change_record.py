from datetime import datetime
from app import db

class ChangeRecord(db.Model):
    __tablename__ = 'change_records'

    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    change_type = db.Column(db.String(50), default='content_changed')  # content_changed, keyword_matched
    content_before = db.Column(db.Text)
    content_after = db.Column(db.Text)
    diff_content = db.Column(db.Text)  # 存储差异内容
    matched_keywords = db.Column(db.Text)  # 匹配的关键词，JSON格式存储
    notification_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ChangeRecord {self.id}: {self.change_type}>'

    def to_dict(self):
        return {
            'id': self.id,
            'website_id': self.website_id,
            'change_type': self.change_type,
            'diff_content': self.diff_content,
            'matched_keywords': self.matched_keywords,
            'notification_sent': self.notification_sent,
            'created_at': self.created_at.isoformat()
        }