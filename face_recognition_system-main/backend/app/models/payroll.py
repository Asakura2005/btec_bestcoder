# backend/app/models/payroll.py

from app.db import db
from datetime import datetime
import pytz
import uuid


class PayrollConfig(db.Model):
    """Cấu hình lương"""
    __tablename__ = 'payroll_config'
    
    id = db.Column(db.Integer, primary_key=True)
    base_salary = db.Column(db.Float, default=10000000, nullable=False)  # Lương cơ bản (VNĐ)
    ot_multiplier = db.Column(db.Float, default=1.5, nullable=False)  # Hệ số OT
    late_deduction = db.Column(db.Float, default=50000, nullable=False)  # Trừ mỗi lần đi trễ
    absent_deduction_rate = db.Column(db.Float, default=1.0, nullable=False)  # Hệ số trừ vắng (1 = trừ 1 ngày lương)
    working_days_per_month = db.Column(db.Integer, default=22, nullable=False)  # Ngày công chuẩn
    updated_at = db.Column(db.DateTime,
                          default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None),
                          onupdate=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None))
    
    @classmethod
    def get_current(cls):
        """Lấy cấu hình hiện tại, tạo mới nếu chưa có"""
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config
    
    def to_dict(self):
        return {
            "base_salary": self.base_salary,
            "ot_multiplier": self.ot_multiplier,
            "late_deduction": self.late_deduction,
            "absent_deduction_rate": self.absent_deduction_rate,
            "working_days_per_month": self.working_days_per_month,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PayrollRecord(db.Model):
    """Bản ghi lương hàng tháng"""
    __tablename__ = 'payroll_records'
    
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    employee_id = db.Column(db.String(8), db.ForeignKey('employees.employee_id'),
                           nullable=False, index=True)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # Attendance data
    working_days_standard = db.Column(db.Integer, default=22)  # Ngày công chuẩn
    actual_work_days = db.Column(db.Float, default=0)  # Ngày công thực tế
    late_count = db.Column(db.Integer, default=0)
    absent_days = db.Column(db.Integer, default=0)
    ot_hours = db.Column(db.Float, default=0)
    
    # Salary calculation
    base_salary = db.Column(db.Float, default=0)  # Lương cơ bản
    daily_rate = db.Column(db.Float, default=0)  # Lương theo ngày
    work_salary = db.Column(db.Float, default=0)  # Lương công thực tế
    ot_pay = db.Column(db.Float, default=0)  # Tiền OT
    late_deductions = db.Column(db.Float, default=0)  # Trừ đi trễ
    absent_deductions = db.Column(db.Float, default=0)  # Trừ vắng mặt
    gross_salary = db.Column(db.Float, default=0)  # Tổng lương trước trừ
    total_deductions = db.Column(db.Float, default=0)  # Tổng khấu trừ
    net_salary = db.Column(db.Float, default=0)  # Lương thực nhận
    
    status = db.Column(db.String(20), default='draft', nullable=False)  # draft, confirmed, paid
    created_at = db.Column(db.DateTime,
                          default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None),
                          nullable=False)
    
    # Unique constraint: 1 record per employee per month
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'month', 'year', name='uq_payroll_emp_month'),
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.payroll_id:
            self.payroll_id = str(uuid.uuid4())
    
    def to_dict(self):
        return {
            "payroll_id": self.payroll_id,
            "employee_id": self.employee_id,
            "month": self.month,
            "year": self.year,
            "working_days_standard": self.working_days_standard,
            "actual_work_days": self.actual_work_days,
            "late_count": self.late_count,
            "absent_days": self.absent_days,
            "ot_hours": round(self.ot_hours, 2),
            "base_salary": self.base_salary,
            "daily_rate": round(self.daily_rate, 0),
            "work_salary": round(self.work_salary, 0),
            "ot_pay": round(self.ot_pay, 0),
            "late_deductions": round(self.late_deductions, 0),
            "absent_deductions": round(self.absent_deductions, 0),
            "gross_salary": round(self.gross_salary, 0),
            "total_deductions": round(self.total_deductions, 0),
            "net_salary": round(self.net_salary, 0),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
