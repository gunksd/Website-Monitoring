from datetime import datetime
from app import db

class Keyword(db.Model):
    __tablename__ = 'keywords'

    id = db.Column(db.Integer, primary_key=True)
    website_id = db.Column(db.Integer, db.ForeignKey('websites.id'), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Keyword {self.keyword}>'

    def to_dict(self):
        return {
            'id': self.id,
            'keyword': self.keyword,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }