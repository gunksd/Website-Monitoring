from datetime import datetime
from app import db

class Website(db.Model):
    __tablename__ = 'websites'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False, unique=True)
    check_interval = db.Column(db.Integer, default=300)  # 检查间隔(秒)
    is_active = db.Column(db.Boolean, default=True)
    last_checked = db.Column(db.DateTime)
    last_content_hash = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    change_records = db.relationship('ChangeRecord', backref='website', lazy=True, cascade='all, delete-orphan')
    keywords = db.relationship('Keyword', backref='website', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Website {self.name}: {self.url}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'url': self.url,
            'check_interval': self.check_interval,
            'is_active': self.is_active,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None,
            'created_at': self.created_at.isoformat(),
            'keywords': [kw.to_dict() for kw in self.keywords]
        }