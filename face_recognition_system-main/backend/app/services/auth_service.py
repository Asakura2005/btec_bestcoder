from datetime import datetime, timedelta
from typing import Tuple, Optional, Union
import pytz
import jwt
import uuid

from app.db import db
from app.models.admin import Admin
from app.models.employee import Employee 
from app.models.audit_log import AuditLog
from app.models.session import Session
from app.utils.security import generate_jwt_token
from app.config import Config 
from app.services.email_service import send_password_reset_email

VN_TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")

# Hàm hỗ trợ khóa tài khoản chung cho cả Admin và Employee
def _lock_account(user_obj: Union[Admin, Employee], duration_minutes: int) -> None:
    """Khóa tài khoản của Admin hoặc Employee trong thời gian nhất định."""
    user_obj.locked_until = datetime.now(VN_TIMEZONE).replace(tzinfo=None) + timedelta(minutes=duration_minutes)
    user_obj.failed_attempts = 0 # Reset failed attempts khi khóa
    db.session.commit()
    # Có thể thêm AuditLog ở đây nếu muốn log việc khóa tài khoản

def login_admin(
        username: str,
        password: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Đăng nhập Admin.
    Returns:
        token (str | None), error (str | None)
    """
    admin: Admin | None = Admin.query.filter_by(username=username).first()
    if not admin: 
        return None, "Invalid username or password"
    
    now_vn = datetime.now(VN_TIMEZONE).replace(tzinfo=None)
    if admin.locked_until and admin.locked_until > now_vn:
        AuditLog.log_login(
            admin_id=admin.id,
            success=False,
        )
        return None, "Account is locked. Please try again later."
    
    if not admin.check_password(password):
        admin.failed_attempts += 1
        status_msg = "Invalid username or password."

        if admin.failed_attempts >= Config.MAX_LOGIN_ATTEMPTS:
            _lock_account(admin, Config.LOCK_DURATION_MINUTES) # SỬ DỤNG HÀM CHUNG
            status_msg = (
                f"Too many failed login attempts {Config.MAX_LOGIN_ATTEMPTS} times, Your account has been locked for {Config.LOCK_DURATION_MINUTES} minutes."
            )

        db.session.commit()
        AuditLog.log_login(
            admin_id=admin.id,
            success=False,
        )
        return None, status_msg
    
    # Đăng nhập thành công, reset
    admin.failed_attempts = 0
    admin.locked_until = None
    admin.last_login = now_vn # Cập nhật last_login

    Session.query.filter_by(admin_id=admin.id, is_valid=True).update({'is_valid': False})
    db.session.commit()

    # Tạo JWT token
    token = generate_jwt_token({'user_id': admin.id, 'role': 'admin'}) # Payload cho Admin

    # Ghi session (SỬ DỤNG PHƯƠNG THỨC create_session MỚI)
    session = Session.create_session(
        admin_id=admin.id,
        jwt_token=token,
        is_admin_session=True,
    )

    # Ghi log
    AuditLog.log_login(
        admin_id=admin.id,
        success=True,
    )

    return token, None

# CẬP NHẬT: login_employee để trả về must_change_password
def login_employee(employee_id_or_email: str, password: str) -> Tuple[Optional[str], Optional[str], Optional[bool]]:
    """
    Đăng nhập Nhân viên. Dùng employee_id (in hoa) hoặc email (in thường).
    """
    username_input = employee_id_or_email.strip()
    employee = Employee.query.filter(
        (Employee.employee_id == username_input.upper()) |
        (Employee.email == username_input.lower())
    ).first()

    if not employee:
        return None, "Invalid username or password.", None

    if not employee.status:
        return None, "Account is disabled. Please contact administrator.", None

    now_vn = datetime.now(VN_TIMEZONE).replace(tzinfo=None)
    if employee.locked_until and employee.locked_until > now_vn:
        return None, "Account is locked. Please try again later.", None

    if not employee.check_password(password):
        employee.failed_attempts += 1
        db.session.commit()

        if employee.failed_attempts >= Config.MAX_LOGIN_ATTEMPTS:
            _lock_account(employee, Config.LOCK_DURATION_MINUTES)
            return None, f"Too many failed login attempts {Config.MAX_LOGIN_ATTEMPTS} times. Account locked for {Config.LOCK_DURATION_MINUTES} minutes.", None

        return None, "Invalid username or password.", None

    # Đăng nhập thành công
    employee.failed_attempts = 0
    employee.locked_until = None
    employee.last_login = now_vn
    db.session.commit()

    token = generate_jwt_token({
        'employee_id': employee.employee_id,
        'role': 'employee',
        'user_id': employee.id
    })

    Session.query.filter_by(employee_id=employee.id, is_valid=True).update({'is_valid': False})
    db.session.commit()

    Session.create_session(
        employee_id=employee.id,
        jwt_token=token,
        is_admin_session=False,
    )

    return token, None, employee.must_change_password


def set_employee_password(employee_id: str, new_password: str, username: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Thiết lập mật khẩu và username cho nhân viên.
    Nếu username không được cung cấp, sẽ mặc định là employee_id.
    """
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return False, "Employe not found."
    
    if not new_password or len(new_password) < Config.MIN_PASSWORD_LENGTH:
        return False, f"Password must have at least {Config.MIN_PASSWORD_LENGTH} characters."

    if username:
        if username != employee.employee_id and username != employee.email:
            existing_employee_with_username = Employee.query.filter(
                (Employee.employee_id == username.upper()) | (Employee.email == username)
            ).first()
            if existing_employee_with_username and existing_employee_with_username.id != employee.id:
                return False, "Username already exists for another employee. Please select a different username."
        employee.username = username 
    else:
        employee.username = employee.employee_id 

    employee.set_password(new_password)
    employee.updated_at = datetime.now(VN_TIMEZONE).replace(tzinfo=None)
    db.session.commit()
    return True, None

def logout_user(user_jwt_token: str) -> None:
    """Vô hiệu hóa session của người dùng (Admin hoặc Employee)"""
    Session.invalidate_token_hash(user_jwt_token)

def verify_token(jwt_payload: dict) -> Optional[Union[Admin, Employee]]:
    """
    Trả về đối tượng Admin hoặc Employee nếu token hợp lệ & session vẫn active.
    """
    user_id = jwt_payload.get("user_id")
    role = jwt_payload.get("role")
    employee_id_from_payload = jwt_payload.get("employee_id") 

    if user_id is None or role is None:
        return None
    
    user_obj = None
    if role == 'admin':
        user_obj = Admin.query.get(user_id)
    elif role == 'employee':
        user_obj = Employee.query.get(user_id)
    
    if not user_obj:
        return None
    
    hashed = Session.hash_token(jwt_payload["jti"]) if "jti" in jwt_payload else None
    if hashed:
        session_query = Session.query.filter_by(jwt_token_hash=hashed, is_valid=True)
        if role == 'admin':
            session_query = session_query.filter_by(admin_id=user_id, is_admin_session=True)
        elif role == 'employee':
            session_query = session_query.filter_by(employee_id=user_id, is_admin_session=False)

        session = session_query.first()

        if session and not session.is_expired():
            session.update_activity() 
            return user_obj
        
    return None


def forgot_password(email: str, user_type: str) -> Tuple[bool, Optional[str]]:
    """
    Gửi email reset password cho admin hoặc employee
    """
    try:
        # Tìm user theo email
        user_obj = None
        if user_type == 'admin':
            user_obj = Admin.query.filter_by(email=email.lower()).first()
        elif user_type == 'employee':
            user_obj = Employee.query.filter_by(email=email.lower()).first()
        else:
            return False, "Invalid user type"
            
        # Security: Không tiết lộ email có tồn tại hay không
        if not user_obj:
            return True, None
            
        # FIXED: Sử dụng UTC time nhất quán
        now_utc = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        
        # Tạo JWT reset token (expires trong 30 phút)
        reset_payload = {
            'user_id': user_obj.id,
            'user_type': user_type,
            'purpose': 'password_reset',
            'exp': now_utc + timedelta(minutes=30),
            'iat': now_utc,
            'jti': str(uuid.uuid4())  # Thêm JTI để nhất quán
        }
        
        reset_token = jwt.encode(reset_payload, Config.JWT_SECRET_KEY, algorithm='HS256')
        
        user_name = user_obj.username if user_type == 'admin' else user_obj.full_name
        send_password_reset_email(email, reset_token, user_type, user_name)
        
        print(f"Password reset email sent to {email} (user_type: {user_type})")
        return True, None
        
    except Exception as e:
        return False, "Unable to send reset email. Please try again later."


def reset_password_with_token(token: str, new_password: str) -> Tuple[bool, Optional[str]]:
    """
    Reset password bằng JWT token từ email
    """
    try:
        
        # FIXED: Sử dụng function decode từ security.py
        from app.utils.security import decode_jwt_token
        
        payload = decode_jwt_token(token)
        
        if not payload:
            # Fallback: Thử decode trực tiếp để debug
            try:
                payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return False, "Reset link has expired. Please request a new one."
            except jwt.InvalidTokenError as e:
                return False, "Invalid reset link. Please request a new one."
            
        # Kiểm tra purpose
        if payload.get('purpose') != 'password_reset':
            return False, "Invalid reset token."
            
        # Validate password
        if not new_password or len(new_password) < Config.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long."
            
        # Lấy user info từ token
        user_id = payload.get('user_id')
        user_type = payload.get('user_type')
        
        
        if not user_id or not user_type:
            return False, "Invalid reset token."
            
        # Tìm user và update password
        user_obj = None
        if user_type == 'admin':
            user_obj = Admin.query.get(user_id)
        elif user_type == 'employee':
            user_obj = Employee.query.get(user_id)
            
        if not user_obj:
            return False, "User not found."
            
        
        # Update password
        user_obj.set_password(new_password)
        
        # Nếu là employee, reset flag must_change_password
        if user_type == 'employee':
            user_obj.must_change_password = False
            
        # Reset failed attempts và unlock account (nếu bị khóa)
        user_obj.failed_attempts = 0
        user_obj.locked_until = None
        user_obj.updated_at = datetime.now(VN_TIMEZONE).replace(tzinfo=None)
        
        # Vô hiệu hóa tất cả session hiện tại của user này
        if user_type == 'admin':
            Session.query.filter_by(admin_id=user_id, is_valid=True).update({'is_valid': False})
        else:
            Session.query.filter_by(employee_id=user_id, is_valid=True).update({'is_valid': False})
            
        db.session.commit()
        
        print(f"Password reset successfully for {user_type} ID: {user_id}")
        return True, None
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return False, "Unable to reset password. Please try again."