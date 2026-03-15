# Import các thư viện cần thiết
from app.db import db  # SQLAlchemy database instance
from datetime import datetime, timezone, date  # Xử lý thời gian
import uuid  # Tạo ID duy nhất
import pytz  # Xử lý múi giờ

# Model lưu trữ bản ghi chấm công
class Attendance(db.Model):
    __tablename__ = 'attendance'  # Tên bảng trong database
    
    # Các cột trong bảng
    id = db.Column(db.Integer, primary_key=True)  # ID chính, tự động tăng
    attendance_id = db.Column(db.String(36), unique=True, nullable=False, index=True)  # ID duy nhất cho bản ghi
    employee_id = db.Column(db.String(8), db.ForeignKey('employees.employee_id'), 
                           nullable=False, index=True)  # Khóa ngoại liên kết với employees
    timestamp = db.Column(db.DateTime, nullable=False, index=True)  # Thời gian chấm công
    status = db.Column(db.String(10), nullable=False)  # Trạng thái: check-in, check-out
    attendance_type = db.Column(db.String(20), nullable=False, default='normal')  # Loại chấm công: normal, late, half_day, recovered
    location = db.Column(db.String(100))  # Vị trí chấm công (tùy chọn)
    device_info = db.Column(db.String(255))  # Thông tin thiết bị (tùy chọn)
    created_at = db.Column(db.DateTime, 
                          default=lambda: datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None), 
                          nullable=False)  # Thời gian tạo bản ghi
    
    
    def __init__(self, **kwargs):
        """Khởi tạo bản ghi với attendance_id và timestamp mặc định"""
        super().__init__(**kwargs)
        if not self.attendance_id:
            self.attendance_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = self._get_vn_datetime()
    
    def _get_vn_datetime(self):
        """Lấy thời gian hiện tại theo múi giờ Việt Nam (naive datetime)"""
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        return datetime.now(vn_tz).replace(tzinfo=None)
    
    @staticmethod
    def validate_status(status):
        """Validate trạng thái chấm công"""
        if not status:
            raise ValueError("Status cannot be empty")
        
        valid_statuses = ['check-in', 'check-out']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        return True
    
    @staticmethod
    def validate_attendance_type(attendance_type):
        """Validate loại chấm công"""
        if not attendance_type:
            raise ValueError("Attendance type cannot be empty")
        
        valid_types = ['normal', 'late', 'half_day', 'recovered'] 
        if attendance_type not in valid_types:
            raise ValueError(f"Invalid attendance type: {attendance_type}. Must be one of {valid_types}")
        return True
    
    @staticmethod
    def validate_location(location):
        """Validate vị trí chấm công (nếu có)"""
        if location and len(location) > 100:
            raise ValueError("Location must not exceed 100 characters")
        return True
    
    @staticmethod
    def validate_device_info(device_info):
        """Validate thông tin thiết bị (nếu có)"""
        if device_info and len(device_info) > 255:
            raise ValueError("Device info must not exceed 255 characters")
        return True
    
    @staticmethod
    def validate_employee_id(employee_id):
        """Validate employee_id"""
        if not employee_id:
            raise ValueError("Employee ID cannot be empty")
        if len(employee_id) > 8:
            raise ValueError("Employee ID must not exceed 8 characters")
        return True
    
    @classmethod
    def create_attendance(cls, employee_id, status, attendance_type='normal', location=None, device_info=None, timestamp=None):
        """Factory method để tạo bản ghi chấm công"""
        # Validate tất cả input
        cls.validate_employee_id(employee_id)
        cls.validate_status(status)
        cls.validate_attendance_type(attendance_type)
        cls.validate_location(location)
        cls.validate_device_info(device_info)
        
        # Tạo instance
        attendance = cls(
            employee_id=employee_id.upper(),  # Đảm bảo uppercase
            status=status,
            attendance_type=attendance_type,
            location=location,
            device_info=device_info
        )
        
        # Set timestamp nếu được cung cấp
        if timestamp:
            attendance.timestamp = timestamp
        
        return attendance
    
    @classmethod
    def get_today_records(cls, employee_id=None, date_filter=None):
        """Lấy bản ghi chấm công hôm nay hoặc ngày cụ thể theo múi giờ Việt Nam"""
        vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
        
        if date_filter:
            target_date = date_filter
        else:
            target_date = datetime.now(vn_tz).date()
        
        query = cls.query.filter(
            db.func.date(cls.timestamp) == target_date
        )
        
        if employee_id:
            query = query.filter(cls.employee_id == employee_id.upper())
        
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_records_by_date_range(cls, employee_id, start_date, end_date):
        """Lấy bản ghi chấm công trong khoảng thời gian"""
        query = cls.query.filter(
            cls.employee_id == employee_id.upper(),
            db.func.date(cls.timestamp) >= start_date,
            db.func.date(cls.timestamp) <= end_date
        )
        return query.order_by(cls.timestamp.desc()).all()
    
    @classmethod
    def get_latest_record(cls, employee_id):
        """Lấy bản ghi chấm công mới nhất của nhân viên"""
        return cls.query.filter_by(employee_id=employee_id.upper())\
                       .order_by(cls.timestamp.desc()).first()
    
    @classmethod
    def get_records_by_employee_and_date(cls, employee_id: str, target_date: date):
        """Lấy tất cả bản ghi chấm công của một nhân viên trong một ngày cụ thể."""
        return cls.query.filter(
            cls.employee_id == employee_id,
            db.func.date(cls.timestamp) == target_date
        ).order_by(cls.timestamp.asc()).all()

    def is_late(self):
        """Kiểm tra xem có đi muộn không"""
        return self.attendance_type == 'late'
    
    def is_half_day(self):
        """Kiểm tra xem có phải nửa ngày không"""
        return self.attendance_type == 'half_day'
    
    def to_dict(self):
        """Chuyển đổi thành dictionary"""
        return {
            'id': self.id,
            'attendance_id': self.attendance_id,
            'employee_id': self.employee_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'status': self.status,
            'attendance_type': self.attendance_type,
            'location': self.location,
            'device_info': self.device_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """Chuỗi đại diện cho bản ghi chấm công"""
        return f'<Attendance {self.employee_id}: {self.status} ({self.attendance_type}) at {self.timestamp}>'