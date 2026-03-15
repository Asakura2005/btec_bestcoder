from app.db import db
from datetime import datetime, timezone, timedelta
from app.utils.security import hash_password, check_password_hash
import pytz

class Admin(db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    role = db.Column(db.String(32), default='admin', nullable=False)
    last_login = db.Column(db.DateTime, index=True)
    failed_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, 
                          default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None), 
                          nullable=False)
    updated_at = db.Column(db.DateTime, 
                          default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None), 
                          onupdate=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None))

    # Relationships
    sessions = db.relationship('Session', backref='admin', lazy=True)
    logs = db.relationship('AuditLog', backref='admin', lazy=True)
    
    def set_password(self, password):
        """Hash và lưu password"""
        self.password_hash = hash_password(password)
    
    def check_password(self, password):
        """Kiểm tra password - CHỈ kiểm tra, không tăng failed_attempts"""
        return check_password_hash(self.password_hash, password)

    
    # def check_password_hash(self, password_hash, password):
    #     """Tách riêng để có thể tái sử dụng"""
    #     return check_password_hash(password_hash, password)
    
    def is_locked(self):
        """Kiểm tra tài khoản có bị khóa hoặc không hoạt động"""
        if not self.is_active:
            return True
        if self.locked_until:
            now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
            return now < self.locked_until
        return False
    
    def lock_account(self, duration_minutes=30):
        """Khóa tài khoản trong thời gian nhất định"""
        now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
        self.locked_until = now + timedelta(minutes=duration_minutes)
        self.failed_attempts = 0
        db.session.commit()
    
    def unlock_account(self):
        """Mở khóa tài khoản"""
        self.locked_until = None
        self.failed_attempts = 0
        db.session.commit()
    
    def __repr__(self):
        return f'<Admin {self.username}>'