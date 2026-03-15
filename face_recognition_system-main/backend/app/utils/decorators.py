# app/utils/decorators.py
from functools import wraps
from flask import request, jsonify
import jwt # THƯ VIỆN PYJWT
from datetime import datetime, timedelta # THÊM IMPORT NÀY
from typing import Optional, Union # THÊM IMPORT NÀY

from app.config import Config # Đảm bảo Config chứa JWT_SECRET_KEY
from app.db import db # THÊM IMPORT NÀY
from app.models.admin import Admin
from app.models.employee import Employee # THÊM IMPORT NÀY
from app.models.session import Session # THÊM IMPORT NÀY
from app.utils.security import hash_password # THÊM IMPORT NÀY (để hash jti)
import pytz

# Hằng số múi giờ Việt Nam
VN_TIMEZONE = pytz.timezone("Asia/Ho_Chi_Minh")

def token_required(f):
    """
    Decorator chung để xác thực JWT token và kiểm tra session trong DB.
    Gắn đối tượng người dùng (Admin hoặc Employee) vào request.current_user
    và vai trò vào request.current_user_role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        
        token = None
        # Lấy token từ header Authorization
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            
            if auth_header.startswith('Bearer '):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"message": "Authentication token is missing!"}), 401

        try:
            # Giải mã token
            data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=["HS256"])
            
            user_id = data.get("user_id")
            role = data.get("role")
            jti = data.get("jti")
            

            if user_id is None or role is None or jti is None:
                return jsonify({"message": "Invalid token (missing user information, role, or JTI)!"}), 401
            
            user_obj = None
            if role == 'admin':
                user_obj = Admin.query.get(user_id)
            elif role == 'employee':
                user_obj = Employee.query.get(user_id)
            
            if not user_obj:
                return jsonify({"message": "User does not exist"}), 401
        
            
            try:
                hashed_jti = Session.hash_token(jti)
            except Exception as hash_error:
                return jsonify({"message": f"Session processing error: {str(hash_error)}"}), 500

            session_query = Session.query.filter_by(jwt_token_hash=hashed_jti, is_valid=True)
            
            if role == 'admin':
                session_query = session_query.filter_by(admin_id=user_obj.id, is_admin_session=True)
            elif role == 'employee':
                session_query = session_query.filter_by(employee_id=user_obj.id, is_admin_session=False)

            session = session_query.first()
            
            if session:
                is_expired = session.is_expired()

            if not session or session.is_expired():
                if session:
                    session.invalidate()
                    db.session.commit()
                return jsonify({"message": "Session has expired or is invalid. Please log in again."}), 401
            
            session.update_activity(extend_duration=True)

            # Gắn đối tượng người dùng và vai trò vào request
            request.current_user = user_obj
            request.current_user_role = role
            
            print("Authentication successful")

        except jwt.ExpiredSignatureError as e:
            return jsonify({"message": "Session has expired. Please log in again.."}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"message": "Session is invalid. Please log in again."}), 401
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"message": f"Authentication error occurred: {str(e)}"}), 500

        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorator để đảm bảo chỉ Admin đã xác thực mới có thể truy cập route.
    """
    @wraps(f)
    @token_required # Yêu cầu token hợp lệ trước
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user_role') or request.current_user_role != 'admin':
            return jsonify({"message": "Admin privileges required!"}), 403
        return f(*args, **kwargs)
    return decorated_function

def employee_required(f):
    """
    Decorator để đảm bảo chỉ Nhân viên đã xác thực mới có thể truy cập route.
    """
    @wraps(f)
    @token_required # Yêu cầu token hợp lệ trước
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user_role') or request.current_user_role != 'employee':
            return jsonify({"message": "Employee privileges required."}), 403
        return f(*args, **kwargs)
    return decorated_function