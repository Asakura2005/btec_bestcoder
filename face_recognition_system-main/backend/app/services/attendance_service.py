# backend/app/services/attendance_service.py - FIXED RESPONSE FORMAT

from datetime import datetime, timedelta, time
import pytz
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import os
from app.db import db
from app.services.facial_service import FacialRecognitionService
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.face_training_data import FaceTrainingData
from app.models.settings import Settings
from app.utils.helpers import get_vn_datetime, format_datetime_vn, format_time_vn, get_upload_path

def recognize_face_logic(image_file, base64_image, location, device_info, session_id: str):
    """Logic nhận diện khuôn mặt và ghi nhận chấm công với settings validation"""
    # Kiểm tra đầu vào
    if not image_file and not base64_image:
        return None, {
            "success": False,
            "message": "No image provided", 
            "liveness_passed": False
        }, 400

    # Kiểm tra session_id
    if not session_id:
        return None, {
            "success": False,
            "message": "Session ID is required",
            "liveness_passed": False
        }, 400

    # Lấy settings hiện tại
    settings = Settings.get_current_settings()

    # Đọc & chuẩn hóa ảnh
    try:
        if base64_image:
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]
            raw_bytes = base64.b64decode(base64_image)
        else:
            raw_bytes = image_file.read()

        nparr = np.frombuffer(raw_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            return None, {
                "success": False,
                "message": "Cannot decode image",
                "liveness_passed": False
            }, 400
    except Exception as e:
        return None, {
            "success": False,
            "message": f"Invalid image input: {str(e)}",
            "liveness_passed": False
        }, 400

    # Nhận diện khuôn mặt WITH LIVENESS
    success, message, employee = FacialRecognitionService.recognize_face_with_liveness(image, session_id)
    
    # CRITICAL: Kiểm tra liveness trước
    if not success:
        # Xác định xem có phải lỗi liveness không
        is_liveness_error = any(keyword in message.lower() for keyword in [
            'blink', 'smile', 'head', 'liveness', 'lighting', 'face'
        ])
        
        return None, {
            "success": False,
            "message": message,
            "liveness_passed": not is_liveness_error,
            "session_id": session_id
        }, 200  # 200 vì đây là response bình thường cho liveness check

    if not employee:
        return None, {
            "success": False,
            "message": "Employee not found from face recognition",
            "liveness_passed": True,  # Liveness OK nhưng không nhận diện được
            "session_id": session_id
        }, 200

    employee_id = employee.employee_id
    full_name = employee.full_name
    department = employee.department
    
    # Extract AI recognition metadata
    recognition_meta = getattr(employee, '_recognition_meta', {})
    detected_emotion = recognition_meta.get('emotion', 'neutral')
    detected_masked = recognition_meta.get('is_masked', False)
    match_distance = recognition_meta.get('match_distance', None)
    confidence_score = recognition_meta.get('confidence_score', None)

    # Lấy thời gian hiện tại
    current_time = get_vn_datetime()
    current_date = current_time.date()
    current_hour = current_time.time()

    # Lấy log chấm công hôm nay
    records_today = Attendance.get_today_records(employee_id=employee_id)
    
    # Lấy check-in và check-out records
    checkin_record = None
    checkout_record = None
    
    for record in records_today:
        if record.status == "check-in":
            checkin_record = record
        elif record.status == "check-out":
            checkout_record = record

    # Kiểm tra policy constraints nếu enabled
    if settings.enable_policies:
        checkin_count = len([r for r in records_today if r.status == "check-in"])
        checkout_count = len([r for r in records_today if r.status == "check-out"])
        
        if checkin_count >= settings.max_checkins_per_day and not checkin_record:
            return None, {
                "success": False,
                "message": f"Maximum check-ins per day ({settings.max_checkins_per_day}) exceeded",
                "liveness_passed": True,
                "session_id": session_id
            }, 400
            
        if checkout_count >= settings.max_checkouts_per_day and checkin_record:
            return None, {
                "success": False,
                "message": f"Maximum check-outs per day ({settings.max_checkouts_per_day}) exceeded",
                "liveness_passed": True,
                "session_id": session_id
            }, 400

    # LOGIC CHẤM CÔNG MỚI
    try:
        # Case 5: Đã đủ cả check-in và check-out
        if checkin_record and checkout_record:
            return {
                "success": True,
                "message": "Already checked in and out today",
                "records_today": [
                    {
                        "status": r.status,
                        "attendance_type": r.attendance_type,
                        "timestamp": format_datetime_vn(r.timestamp)
                    } for r in records_today
                ],
                "liveness_passed": True,
                "session_id": session_id
            }, None, 200

        # Case 1: Check-in bình thường (chưa có check-in)
        if not checkin_record:
            # Xác định attendance_type
            attendance_type = "normal"
            
            # Kiểm tra muộn
            if current_hour > settings.start_work:
                # Kiểm tra có trong giờ nghỉ trưa không
                if settings.lunch_start <= current_hour <= settings.lunch_end:
                    attendance_type = "half_day"
                else:
                    attendance_type = "late"
            
            # Tạo record check-in
            attendance = Attendance.create_attendance(
                employee_id=employee_id,
                status="check-in",
                timestamp=current_time,
                attendance_type=attendance_type
            )
            # Save AI metadata
            attendance.emotion = detected_emotion
            attendance.is_masked = detected_masked
            db.session.add(attendance)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Attendance recorded successfully",
                "employee": {
                    "employee_id": employee_id,
                    "full_name": full_name,
                    "department": department
                },
                "status": "check-in",
                "attendance_type": attendance_type,
                "timestamp": format_datetime_vn(current_time),
                "emotion": detected_emotion,
                "is_masked": detected_masked,
                "confidence_score": confidence_score,
                "liveness_passed": True,
                "session_id": session_id
            }, None, 200

        # Case 2: Check-out bình thường (đã có check-in, chưa có check-out)
        elif checkin_record and not checkout_record:
            # Tạo record check-out với attendance_type giống check-in
            attendance = Attendance.create_attendance(
                employee_id=employee_id,
                status="check-out",
                timestamp=current_time,
                attendance_type=checkin_record.attendance_type
            )
            db.session.add(attendance)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Attendance recorded successfully",
                "employee": {
                    "employee_id": employee_id,
                    "full_name": full_name,
                    "department": department
                },
                "status": "check-out",
                "attendance_type": checkin_record.attendance_type,
                "timestamp": format_datetime_vn(current_time),
                "liveness_passed": True,
                "session_id": session_id
            }, None, 200

        # Case 3: Quên check-in, chỉ checkout (sau giờ làm việc)
        elif not checkin_record and current_hour >= settings.end_work:
            # Tạo record check-out incomplete
            attendance = Attendance.create_attendance(
                employee_id=employee_id,
                status="check-out",
                timestamp=current_time,
                attendance_type="incomplete"
            )
            db.session.add(attendance)
            db.session.commit()
            
            return {
                "success": True,
                "message": "Attendance recorded successfully",
                "employee": {
                    "employee_id": employee_id,
                    "full_name": full_name,
                    "department": department
                },
                "status": "check-out",
                "attendance_type": "incomplete",
                "timestamp": format_datetime_vn(current_time),
                "warning": "Missing check-in record",
                "liveness_passed": True,
                "session_id": session_id
            }, None, 200

        # Trường hợp khác: Không xác định được hành động
        else:
            return None, {
                "success": False,
                "message": "Cannot determine attendance action at this time",
                "liveness_passed": True,
                "session_id": session_id
            }, 400

    except Exception as e:
        db.session.rollback()
        return None, {
            "success": False,
            "message": f"Database error: {str(e)}",
            "liveness_passed": True,
            "session_id": session_id
        }, 500

def get_attendance_history_logic(employee_id):
    """Lấy lịch sử chấm công của nhân viên"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {
            "success": False,
            "message": "Employee not found"
        }, 404
    
    records = Attendance.query.filter_by(employee_id=employee_id.upper())\
        .order_by(Attendance.timestamp.desc()).limit(50).all()
    
    result = []
    for record in records:
        result.append({
            "attendance_id": record.attendance_id,
            "status": record.status,
            "attendance_type": record.attendance_type,
            "timestamp": format_datetime_vn(record.timestamp),
        })
    
    return {
        "success": True,
        "employee": {
            "employee_id": employee.employee_id,
            "full_name": employee.full_name
        },
        "records": result,
        "total": len(result)
    }, None, 200

def get_today_attendance_logic(employee_id):
    """Lấy chấm công hôm nay của nhân viên"""
    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {
            "success": False,
            "message": "Employee not found"
        }, 404
    
    records_today = Attendance.get_today_records(employee_id=employee_id.upper())
    
    result = []
    for record in records_today:
        result.append({
            "status": record.status,
            "attendance_type": record.attendance_type,
            "timestamp": format_datetime_vn(record.timestamp)
        })
    
    statuses = [r.status for r in records_today]
    if "check-in" not in statuses:
        current_status = "not_checked_in"
    elif "check-out" not in statuses:
        current_status = "checked_in"
    else:
        current_status = "completed"
    
    return {
        "success": True,
        "employee": {
            "employee_id": employee.employee_id,
            "full_name": employee.full_name
        },
        "current_status": current_status,
        "records_today": result,
        "total_records": len(result)
    }, None, 200

def capture_face_training_logic(image_file, base64_image, employee_id, pose_type):
    """Logic capture ảnh training cho nhân viên"""
    if not employee_id:
        return None, {
            "success": False,
            "message": "Missing employee_id"
        }, 400
    if not image_file and not base64_image:
        return None, {
            "success": False,
            "message": "No image provided",
            "error": "No image provided"
        }, 400
    if not pose_type:
        return None, {
            "success": False,
            "message": "Missing pose_type"
        }, 400

    # Validate pose_type
    try:
        FaceTrainingData.validate_pose_type(pose_type)
    except ValueError as e:
        return None, {
            "success": False,
            "message": str(e)
        }, 400

    employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
    if not employee:
        return None, {
            "success": False,
            "message": "Employee not found"
        }, 404

    # Đọc & chuẩn hóa ảnh
    try:
        if base64_image:
            if base64_image.startswith('data:'):
                base64_image = base64_image.split(',', 1)[1]
            raw_bytes = base64.b64decode(base64_image)
        else:
            raw_bytes = image_file.read()

        nparr = np.frombuffer(raw_bytes, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_cv is None:
            return None, {
                "success": False,
                "message": "Cannot decode image"
            }, 400

        ok, buf = cv2.imencode(".jpg", img_cv, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not ok:
            return None, {
                "success": False,
                "message": "Failed to encode image"
            }, 400
        image_data = BytesIO(buf.tobytes())
    except (base64.binascii.Error, ValueError) as e:
        return None, {
            "success": False,
            "message": f"Image processing error: {str(e)}"
        }, 400

    # Sinh face-encoding & metadata với employee_id
    success, message, encoding, metadata = (
        FacialRecognitionService.generate_face_encoding_with_metadata(
            image_data, 
            pose_type=pose_type,
            employee_id=employee_id.upper()
        )
    )
    if not success:
        return None, {
            "success": False,
            "message": message,
            "error": message
        }, 400

    # Lưu ảnh gốc
    try:
        image_data.seek(0)
        img_pil = Image.open(image_data).convert("RGB")
        save_dir = get_upload_path()
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{employee_id}_{metadata['pose_type']}.jpg")
        img_pil.save(save_path, quality=90)
    except Exception as e:
        return None, {
            "success": False,
            "message": f"Save image failed: {str(e)}"
        }, 500

    # Ghi dữ liệu training
    try:
        existing_training = FaceTrainingData.query.filter_by(
            employee_id=employee_id.upper(), 
            pose_type=metadata['pose_type']
        ).first()
        
        if existing_training:
            existing_training.face_encoding = encoding
            existing_training.image_quality_score = metadata['image_quality_score']
            existing_training.created_at = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh")).replace(tzinfo=None)
            print(f"Cập nhật pose {metadata['pose_type']} cho {employee_id}")
        else:
            training_data = FaceTrainingData.create_training_data(
                employee_id=employee_id.upper(),
                pose_type=metadata['pose_type'],
                face_encoding=encoding,
                image_quality_score=metadata['image_quality_score']
            )
            db.session.add(training_data)
            print(f"Tạo pose mới {metadata['pose_type']} cho {employee_id}")
        
        db.session.commit()
        updated_progress = employee.get_face_training_progress()
        
        print(f"Progress của {employee_id}: {updated_progress['poses_completed']}/{updated_progress['poses_required']} - Completed: {employee.face_training_completed}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Database error: {e}")
        return None, {
            "success": False,
            "message": f"Database error: {str(e)}"
        }, 500

    return {
        "success": True,
        "message": "Pose captured successfully",
        "pose_type": metadata['pose_type'],
        "progress": updated_progress,
        "employee_id": employee_id.upper()
    }, None, 200