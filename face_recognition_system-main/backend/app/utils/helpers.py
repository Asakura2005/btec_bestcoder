# backend/app/utils/helpers.py

# Tiện ích khác (format ngày giờ, export file...)
import pytz
from datetime import datetime
import os
from flask import current_app 

def format_datetime_vn(dt):
    if dt is None:
        return None
    
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    dt_vn = vn_tz.localize(dt)
    return dt_vn.strftime("%d/%m/%Y %H:%M:%S")

def get_vn_datetime():
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(vn_tz).replace(tzinfo=None)


def format_time_vn(dt):
    if dt is None:
        return None
    return dt.strftime("%H:%M:%S")


def get_upload_path():

    backend_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
    
    # Sau đó, nối với 'data/uploads' để tạo đường dẫn đích
    upload_dir = os.path.join(backend_root, 'data', 'uploads')
    return upload_dir

def get_export_path():
    """Tạo đường dẫn thư mục exports để lưu file báo cáo Excel"""
    try:
        # Lấy đường dẫn gốc của backend
        backend_root = os.path.abspath(os.path.join(current_app.root_path, '..'))
        
        # Nối với 'data/exports' để tạo đường dẫn đích
        export_dir = os.path.join(backend_root, 'data', 'exports')
        
        # Tạo thư mục nếu chưa tồn tại
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
    
        
        # Kiểm tra quyền ghi
        if not os.access(export_dir, os.W_OK):
            print(f"WARNING: No write permission for export directory: {export_dir}")
        
        return export_dir
    
    except Exception as e:
        print(f"ERROR in get_export_path: {str(e)}")
        # Fallback - tạo trong thư mục tạm thời
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), 'attendance_exports')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

def serialize_employee_full(employee):
    image_filename = f"{employee.employee_id}.jpg"
    image_path_on_disk = os.path.join(get_upload_path(), image_filename)
    
    image_url = f"/uploads/{image_filename}" if os.path.exists(image_path_on_disk) else None

    return {
        "id": employee.id,
        "employee_id": employee.employee_id,
        "full_name": employee.full_name,
        "department": employee.department,
        "position": employee.position,
        "phone": employee.phone, 
        "email": employee.email, 
        "status": employee.status, 
        "created_at": format_datetime_vn(employee.created_at),
        "updated_at": format_datetime_vn(employee.updated_at),
        "imageUrl": image_url 
    }
