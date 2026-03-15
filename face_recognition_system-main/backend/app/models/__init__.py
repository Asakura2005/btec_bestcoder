# Import tất cả các model để Flask-Migrate tự động nhận diện khi migrate
from .employee import Employee
from .attendance import Attendance
from .admin import Admin
from .session import Session
from .audit_log import AuditLog
from .face_training_data import FaceTrainingData
from .attendance_recovery import AttendanceRecoveryRequest
