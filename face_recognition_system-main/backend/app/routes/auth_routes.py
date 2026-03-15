# API login/logout
from flask import Blueprint, request, jsonify
from app.services.auth_service import login_admin, login_employee, logout_user, forgot_password, reset_password_with_token
from app.models.admin import Admin
from app.models.employee import Employee 
from app.db import db
from app.utils.decorators import token_required 

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/admin/login", methods=["POST"]) # ĐỔI TÊN ROUTE ĐỂ RÕ RÀNG HƠN CHO ADMIN
def admin_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(error="Username or password can not be empty."), 400

    token, err = login_admin(username, password)
    if err:
        return jsonify(error=err), 401

    return jsonify(token=token, username=username, role="admin"), 200

@auth_bp.route("/employee/login", methods=["POST"])
def employee_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip() # Có thể là employee_id hoặc email
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify(error="Username or password must not be empty."), 400

    token, err, must_change_password = login_employee(username, password)
    if err:
        return jsonify(error=err), 401
    
    employee = Employee.query.filter((Employee.employee_id == username.upper()) | (Employee.email == username)).first()
    
    return jsonify(
        token=token, 
        employee_id=employee.employee_id if employee else None, 
        full_name=employee.full_name if employee else None, 
        role="employee",
        must_change_password=must_change_password
    ), 200

# CẬP NHẬT: Route verify chung cho cả Admin và Employee
@auth_bp.route("/verify", methods=["GET"])
@token_required 
def verify():
    # request.current_user và request.current_user_role được set bởi @token_required
    user = request.current_user
    role = request.current_user_role

    if role == 'admin':
        return jsonify(valid=True, user_id=user.id, username=user.username, role=role), 200
    elif role == 'employee':
        return jsonify(valid=True, user_id=user.id, employee_id=user.employee_id, full_name=user.full_name, role=role), 200
    else:
        return jsonify(valid=False, message="Invalid user role"), 400

# CẬP NHẬT: Route logout chung
@auth_bp.route("/logout", methods=["POST"])
@token_required 
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    logout_user(token) # SỬ DỤNG HÀM LOGOUT CHUNG
    return jsonify(msg="Logout successfully"), 200

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password_route():
    """
    Gửi email reset password
    Body: {
        "email": "user@example.com",
        "user_type": "admin" | "employee"  # Được xác định từ tab frontend
    }
    """
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    user_type = data.get("user_type", "").strip().lower()
    
    # Validation
    if not email:
        return jsonify(error="Email is required"), 400
        
    if user_type not in ['admin', 'employee']:
        return jsonify(error="Invalid user type"), 400
        
    # Basic email format validation
    if "@" not in email or "." not in email:
        return jsonify(error="Please enter a valid email address"), 400
    
    # Gọi service
    success, error = forgot_password(email, user_type)
    
    if not success and error:
        return jsonify(error=error), 500
    
    # Luôn trả về success message (bảo mật)
    return jsonify(
        message="If your email exists in our system, you will receive a password reset link.",
        email=email  # Frontend có thể hiển thị email đã gửi
    ), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password_route():
    """
    Reset password bằng token từ email
    Body: {
        "token": "jwt_token_from_email",
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token", "").strip()
    new_password = data.get("new_password", "").strip()
    confirm_password = data.get("confirm_password", "").strip()
    
    # Validation
    if not token:
        return jsonify(error="Reset token is required"), 400
        
    if not new_password or not confirm_password:
        return jsonify(error="Both password fields are required"), 400
        
    if new_password != confirm_password:
        return jsonify(error="Passwords do not match"), 400
    
    # Gọi service
    success, error = reset_password_with_token(token, new_password)
    
    if not success:
        return jsonify(error=error), 400
        
    return jsonify(
        message="Your password has been successfully reset! You can now login with your new password."
    ), 200