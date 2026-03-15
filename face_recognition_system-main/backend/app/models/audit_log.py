from app.db import db
from datetime import datetime, timezone, timedelta
import pytz

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False, index=True)
    action = db.Column(db.String(64), nullable=False, index=True)
    target_type = db.Column(db.String(32))  # 'employee', 'admin', 'system'
    target_id = db.Column(db.String(32))
    details = db.Column(db.Text)  # Giới hạn độ dài trong validation
    timestamp = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), default='success')  # 'success', 'failed', 'warning'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.timestamp:
            # Đồng bộ timezone với Employee và Attendance - sử dụng Asia/Ho_Chi_Minh
            self.timestamp = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    
    @staticmethod
    def validate_status(status):
        """Validate status"""
        valid_statuses = ['success', 'failed', 'warning']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return True
    
    @staticmethod
    def validate_details(details):
        """Validate details length"""
        if details and len(details) > 1000:
            raise ValueError("Details must not exceed 1000 characters")
        return True
    
    @classmethod
    def log_action(cls, admin_id, action, details=None, target_type=None, target_id=None, 
                    status='success'):
        """Helper method để tạo audit log"""
        cls.validate_status(status)
        cls.validate_details(details)
        
        log = cls(
            admin_id=admin_id,
            action=action,
            details=details,
            target_type=target_type,
            target_id=target_id,
            status=status
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @classmethod
    def log_login(cls, admin_id, success=True):
        """Log login attempt"""
        return cls.log_action(
            admin_id=admin_id,
            action='login',
            details='User login attempt',
            status='success' if success else 'failed'
        )
    
    @classmethod
    def log_employee_action(cls, admin_id, action, employee_id, details=None
                            ):
        """Log employee-related actions"""
        return cls.log_action(
            admin_id=admin_id,
            action=action,
            target_type='employee',
            target_id=employee_id,
            details=details,
        )
    
    @classmethod
    def get_recent_logs(cls, limit=50, admin_id=None, action=None):
        """Lấy logs gần đây"""
        query = cls.query
        if admin_id:
            query = query.filter(cls.admin_id == admin_id)
        if action:
            query = query.filter(cls.action == action)
        return query.order_by(cls.timestamp.desc()).limit(limit).all()
    
    @classmethod
    def archive_old_logs(cls, days=90):
        """Lưu trữ hoặc xóa logs cũ hơn số ngày quy định"""
        cutoff = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None) - timedelta(days=days)
        old_logs = cls.query.filter(cls.timestamp < cutoff).all()
        for log in old_logs:
            db.session.delete(log)
        db.session.commit()
        return len(old_logs)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by Admin {self.admin_id} at {self.timestamp}>'