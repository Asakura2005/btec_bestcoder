# Xử lý logic liên quan nhân viên 
# backend/app/services/employee_utils.py

from flask import send_from_directory
from app.models.employee import Employee
from app.models.face_training_data import FaceTrainingData
from app.services.facial_service import FacialRecognitionService
from app.utils.helpers import get_upload_path, serialize_employee_full, format_datetime_vn
from app import db
from sqlalchemy.exc import IntegrityError
from PIL import Image
from io import BytesIO
import os
import pytz
from datetime import datetime
from typing import Optional, Tuple
from app.services.auth_service import set_employee_password
from app.config import Config 

def serve_uploaded_image_logic(filename):
    """Logic phục vụ ảnh từ thư mục uploads"""
    upload_folder = get_upload_path()
    try:
        return send_from_directory(upload_folder, filename), None, None
    except Exception:
        return None, {"error": "File not found or cannot be served"}, 404

# CẬP NHẬT: add_employee_logic để hỗ trợ đặt mật khẩu mặc định và cờ must_change_password
def add_employee_logic(data, image_files):
    """Logic thêm nhân viên mới với thông tin và ảnh khuôn mặt và mật khẩu ban đầu."""
    required_fields = ['employee_id', 'full_name', 'department']
    for field in required_fields:
        if not data.get(field):
            return None, {"error": f"Missing required field {field}"}, 400

    employee_id = data['employee_id'].upper()
    if Employee.query.filter_by(employee_id=employee_id).first():
        return None, {"error": "Employee ID already exists"}, 400

    try:
        Employee.validate_email(data.get('email'))
        Employee.validate_phone(data.get('phone'))
    except ValueError as ve:
        return None, {"error": str(ve)}, 400

    save_dir = get_upload_path()
    os.makedirs(save_dir, exist_ok=True)
    required_poses = FacialRecognitionService.get_required_poses()
    pose_types = []
    face_encodings = []

    try:
        for i, image_file in enumerate(image_files):
            pose_type = required_poses[i % len(required_poses)] if i < len(required_poses) else 'front'
            success, message, encoding, metadata = FacialRecognitionService.generate_face_encoding_with_metadata(image_file, pose_type)
            if not success:
                return None, {"error": message}, 400
            face_encodings.append((encoding, metadata['pose_type'], metadata['image_quality_score']))
            image_file.stream.seek(0)
            image = Image.open(BytesIO(image_file.read())).convert("RGB")
            save_path = os.path.join(save_dir, f"{employee_id}_{pose_type}.jpg")
            image.save(save_path)
            pose_types.append(metadata['pose_type'])
    except Exception as e:
        return None, {"error": f"Failed to process images: {str(e)}"}, 500

    new_employee = Employee(
        employee_id=employee_id,
        full_name=data['full_name'],
        department=data['department'],
        position=data.get('position'),
        phone=data.get('phone'),
        email=data.get('email'),
        face_training_completed=len(pose_types) >= 3,
        total_poses_trained=len(pose_types),
        username=data.get('username') # Admin có thể cung cấp username riêng
    )
    
    # Logic đặt mật khẩu mặc định và cờ must_change_password
    initial_password = data.get('initial_password')
    if initial_password:
        # Nếu Admin cung cấp mật khẩu ban đầu, sử dụng nó
        new_employee.set_password(initial_password)
        new_employee.must_change_password = False # Không cần đổi ngay nếu Admin đã đặt
        if not new_employee.username: # Nếu Admin không đặt username, dùng employee_id
            new_employee.username = employee_id
    else:
        # Nếu Admin không cung cấp, đặt mật khẩu mặc định là employee_id và buộc đổi
        new_employee.set_password(employee_id) # Mật khẩu mặc định là employee_id
        new_employee.must_change_password = True # Buộc đổi mật khẩu lần đầu
        if not new_employee.username: # Nếu Admin không đặt username, dùng employee_id
            new_employee.username = employee_id


    try:
        db.session.add(new_employee)
        db.session.commit() # Commit để có new_employee.id cho FaceTrainingData

        for encoding, pose_type, quality_score in face_encodings:
            training_data = FaceTrainingData.create_training_data(
                employee_id=employee_id,
                pose_type=pose_type,
                face_encoding=encoding,
                image_quality_score=quality_score
            )
            db.session.add(training_data)
        if len(pose_types) >= 3:
            new_employee.complete_face_training()
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return None, {"error": "Database error – possibly duplicate or constraint violation"}, 500
    except Exception as e:
        db.session.rollback()
        return None, {"error": f"An unexpected error occurred: {str(e)}"}, 500

    return {
        "message": "Employee added successfully",
        "employee": serialize_employee_full(new_employee),
        "poses_trained": pose_types
    }, None, 201

def get_employees_logic(status_param=None, page=1, limit=10, search='', sort_by='created_at', sort_order='desc'):
    """Logic lấy danh sách nhân viên với pagination và search"""
    query = Employee.query
    
    # Filter theo status - SỬA LẠI LOGIC NÀY
    if status_param is not None:
        # Chuyển đổi string thành boolean
        if status_param.lower() in ['true', '1', 'active']:
            query = query.filter_by(status=True)
        elif status_param.lower() in ['false', '0', 'inactive', 'deleted']:
            query = query.filter_by(status=False)
    
    # Search
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Employee.employee_id.like(search_term),
                Employee.full_name.like(search_term),
                Employee.email.like(search_term),
                Employee.department.like(search_term)
            )
        )
    
    # Sorting
    sort_column = getattr(Employee, sort_by, Employee.created_at)
    if sort_order.lower() == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())
    
    # Pagination
    total = query.count()
    employees = query.offset((page - 1) * limit).limit(limit).all()
    
    result = [serialize_employee_full(emp) for emp in employees]
    
    return {
        "employees": result,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }, None, 200

def get_employee_detail_logic(employee_id):
    """Logic lấy chi tiết một nhân viên"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {"error": "Employee not found"}, 404
    return {"employee": serialize_employee_full(employee)}, None, 200

def update_employee_logic(employee_id, data, image_files):
    """Logic cập nhật thông tin nhân viên hoặc ảnh khuôn mặt"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {"error": "Employee not found"}, 404

    if data.get("full_name"):
        employee.full_name = data["full_name"]
    if data.get("department"):
        employee.department = data["department"]
    if data.get("position"):
        employee.position = data["position"]
    if data.get("phone") is not None:
        try:
            Employee.validate_phone(data["phone"])
            employee.phone = data["phone"]
        except ValueError as ve:
            return None, {"error": str(ve)}, 400
    if data.get("email") is not None:
        try:
            Employee.validate_email(data["email"])
            employee.email = data["email"]
        except ValueError as ve:
            return None, {"error": str(ve)}, 400
    if data.get("status") is not None:
        employee.status = data["status"].lower() == 'true'

    pose_types = []
    if image_files:
        save_dir = get_upload_path()
        os.makedirs(save_dir, exist_ok=True)
        required_poses = FacialRecognitionService.get_required_poses()
        face_encodings = []
        try:
            for i, image_file in enumerate(image_files):
                pose_type = required_poses[i % len(required_poses)] if i < len(required_poses) else 'front'
                success, message, encoding, metadata = FacialRecognitionService.generate_face_encoding_with_metadata(image_file, pose_type)
                if not success:
                    return None, {"error": message}, 400
                face_encodings.append((encoding, metadata['pose_type'], metadata['image_quality_score']))
                image_file.stream.seek(0)
                image = Image.open(BytesIO(image_file.read())).convert("RGB")
                save_path = os.path.join(save_dir, f"{employee_id}_{pose_type}.jpg")
                image.save(save_path)
                pose_types.append(metadata['pose_type'])
        except Exception as e:
            return None, {"error": f"Failed to process images: {str(e)}"}, 500
        FaceTrainingData.query.filter_by(employee_id=employee_id).delete()
        for encoding, pose_type, quality_score in face_encodings:
            training_data = FaceTrainingData.create_training_data(
                employee_id=employee_id,
                pose_type=pose_type,
                face_encoding=encoding,
                image_quality_score=quality_score
            )
            db.session.add(training_data)
        employee.face_training_completed = len(pose_types) >= 3
        employee.total_poses_trained = len(pose_types)
        if len(pose_types) >= 3:
            employee.complete_face_training()

    employee.updated_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    db.session.commit()
    return {
        "message": "Employee updated successfully",
        "employee": serialize_employee_full(employee),
        "poses_trained": pose_types if image_files else []
    }, None, 200

def soft_delete_employee_logic(employee_id):
    """Logic đánh dấu nhân viên là inactive (xóa mềm)"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {"error": "Employee not found"}, 404
    if not employee.status:
        return {"message": "Employee is already inactive", "employee": serialize_employee_full(employee)}, None, 200
    employee.status = False
    employee.updated_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    db.session.commit()
    return {
        "message": "Employee soft-deleted successfully",
        "employee": serialize_employee_full(employee)
    }, None, 200

def restore_employee_logic(employee_id):
    """Logic khôi phục nhân viên từ trạng thái inactive"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {"error": "Employee not found"}, 404
    if employee.status:
        return {"message": "Employee is already active", "employee": serialize_employee_full(employee)}, None, 200
    employee.status = True
    employee.updated_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    db.session.commit()
    return {
        "message": f"Employee {employee_id} restored successfully",
        "employee": serialize_employee_full(employee)
    }, None, 200

# THÊM HÀM MỚI: Đặt lại mật khẩu cho nhân viên (Admin dùng)
def set_employee_password_logic(employee_id: str, new_password: str, username: Optional[str] = None):
    """Logic để Admin đặt lại mật khẩu cho nhân viên."""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {"error": "Employee not found."}, 404

    success, message = set_employee_password(employee_id, new_password, username)
    if not success:
        return None, {"error": message}, 400
    
    # Admin đặt lại mật khẩu, có thể không cần buộc đổi lần sau
    employee.must_change_password = False 
    db.session.commit()

    return {
        "message": "Employee password updated successfully.",
        "employee": serialize_employee_full(employee)
    }, None, 200

# THÊM HÀM MỚI: Nhân viên tự đổi mật khẩu
def change_employee_password_by_employee(employee_id: int, old_password: str, new_password: str) -> Tuple[bool, str]:
    """
    Logic cho phép nhân viên tự đổi mật khẩu của mình.
    employee_id ở đây là ID (int) của bảng employees, không phải employee_id (str)
    """
    employee = Employee.query.get(employee_id)
    if not employee:
        return False, "Employee not found."

    # Kiểm tra mật khẩu cũ
    if not employee.check_password(old_password):
        return False, "Old password is wrong."
    
    # Kiểm tra độ dài mật khẩu mới
    if not new_password or len(new_password) < Config.MIN_PASSWORD_LENGTH:
        return False, f"New password must have at least {Config.MIN_PASSWORD_LENGTH} characters."
    
    # Đặt mật khẩu mới
    employee.set_password(new_password)
    employee.must_change_password = False # Đã đổi mật khẩu, không cần buộc đổi nữa
    employee.updated_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
    
    try:
        db.session.commit()
        return True, "Password changed successfully"
    except Exception as e:
        db.session.rollback()
        return False, f"Error occur change password: {str(e)}"