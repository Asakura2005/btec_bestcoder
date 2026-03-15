# app/models/attendance_recovery.py
from app.db import db
from datetime import datetime
import pytz
import uuid

class AttendanceRecoveryRequest(db.Model):
    __tablename__ = 'attendance_recovery_requests'

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    employee_id = db.Column(db.String(8), db.ForeignKey('employees.employee_id'), # Khóa ngoại đến employee_id trong bảng employees
                           nullable=False, index=True)
    request_date = db.Column(db.Date, nullable=False) # Ngày mà nhân viên muốn phục hồi chấm công
    requested_at = db.Column(db.DateTime,
                             default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None),
                             nullable=False)
    reason = db.Column(db.Text, nullable=False) # Lý do phục hồi
    status = db.Column(db.String(20), default='pending', nullable=False) # pending, approved, rejected
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=True) # Admin đã duyệt/từ chối
    approved_at = db.Column(db.DateTime, nullable=True) # Thời gian duyệt/từ chối
    notes = db.Column(db.Text, nullable=True) # Ghi chú của admin

    # Quan hệ
    admin = db.relationship('Admin', backref='approved_recovery_requests', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.request_id:
            self.request_id = str(uuid.uuid4())

    def to_dict(self):
        """Chuyển đổi thành dictionary để dễ dàng trả về qua API"""
        return {
            'id': self.id,
            'request_id': self.request_id,
            'employee_id': self.employee_id,
            'request_date': self.request_date.isoformat() if self.request_date else None,
            'requested_at': self.requested_at.isoformat() if self.requested_at else None,
            'reason': self.reason,
            'status': self.status,
            'admin_id': self.admin_id,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'notes': self.notes
        }

    def __repr__(self):
        return f'<AttendanceRecoveryRequest {self.request_id}: Employee {self.employee_id} - Date {self.request_date} - Status {self.status}>'