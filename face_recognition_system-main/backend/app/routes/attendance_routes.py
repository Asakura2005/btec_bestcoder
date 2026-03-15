# backend/app/routes/attendance_routes.py

from flask import Blueprint, request, jsonify
from app.services.attendance_service import (
    recognize_face_logic,
    get_attendance_history_logic,
    get_today_attendance_logic,
    capture_face_training_logic
)
from app.utils.decorators import admin_required, employee_required

# Khởi tạo Blueprint cho các route chấm công
attendance_bp = Blueprint('attendance_bp', __name__)

@attendance_bp.route('/api/recognize', methods=['POST'])
def recognize_face():
    """Nhận diện khuôn mặt và ghi nhận chấm công"""
    try:
        # Kiểm tra content type để xử lý đúng format
        if request.is_json:
            # Xử lý JSON data từ frontend Vue.js
            data = request.get_json()
            image_file = None
            base64_image = data.get('base64_image')
            location = data.get('location')
            device_info = data.get('device_info')
            session_id = data.get('session_id')
        else:
            # Xử lý FormData (cho các request khác)
            image_file = request.files.get('image')
            base64_image = request.form.get('base64_image')
            location = request.form.get('location')
            device_info = request.form.get('device_info')
            session_id = request.form.get('session_id')

        # Validation
        if not base64_image and not image_file:
            return jsonify({
                'success': False,
                'message': 'No image data provided',
                'liveness_passed': False
            }), 400

        if not session_id:
            return jsonify({
                'success': False,
                'message': 'Session ID is required',
                'liveness_passed': False
            }), 400

        # Gọi logic xử lý
        result, error, status = recognize_face_logic(
            image_file, 
            base64_image, 
            location, 
            device_info, 
            session_id
        )
        
        if error:
            # Đảm bảo error response có format chuẩn
            if isinstance(error, dict):
                return jsonify(error), status
            else:
                return jsonify({
                    'success': False,
                    'message': str(error),
                    'liveness_passed': False
                }), status
        
        # Đảm bảo success response có format chuẩn
        if isinstance(result, dict):
            # Thêm success flag nếu chưa có
            if 'success' not in result:
                result['success'] = True
            return jsonify(result), status
        else:
            return jsonify({
                'success': True,
                'message': str(result),
                'liveness_passed': True
            }), status

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}',
            'liveness_passed': False
        }), 500

@attendance_bp.route('/api/attendance/<string:employee_id>', methods=['GET'])
def get_attendance_history(employee_id):
    """Lấy lịch sử chấm công của nhân viên"""
    try:
        result, error, status = get_attendance_history_logic(employee_id)
        if error:
            if isinstance(error, dict):
                return jsonify(error), status
            else:
                return jsonify({
                    'success': False,
                    'message': str(error)
                }), status
        
        # Đảm bảo response có format chuẩn
        if isinstance(result, dict):
            if 'success' not in result:
                result['success'] = True
            return jsonify(result), status
        else:
            return jsonify({
                'success': True,
                'data': result
            }), status

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@attendance_bp.route('/api/attendance/today/<string:employee_id>', methods=['GET'])
def get_today_attendance(employee_id):
    """Lấy chấm công hôm nay của nhân viên"""
    try:
        result, error, status = get_today_attendance_logic(employee_id)
        if error:
            if isinstance(error, dict):
                return jsonify(error), status
            else:
                return jsonify({
                    'success': False,
                    'message': str(error)
                }), status
        
        if isinstance(result, dict):
            if 'success' not in result:
                result['success'] = True
            return jsonify(result), status
        else:
            return jsonify({
                'success': True,
                'data': result
            }), status

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500

@attendance_bp.route('/api/face-training/capture', methods=['POST'])
def capture_face_training():
    """Capture ảnh training cho nhân viên"""
    try:
        # Xử lý cả JSON và FormData
        if request.is_json:
            data = request.get_json()
            image_file = None
            base64_image = data.get('base64_image')
            employee_id = data.get('employee_id')
            pose_type = data.get('pose_type')
        else:
            image_file = request.files.get('image')
            base64_image = request.form.get('base64_image')
            employee_id = request.form.get('employee_id')
            pose_type = request.form.get('pose_type')

        result, error, status = capture_face_training_logic(
            image_file, 
            base64_image, 
            employee_id, 
            pose_type
        )
        
        if error:
            if isinstance(error, dict):
                return jsonify(error), status
            else:
                return jsonify({
                    'success': False,
                    'message': str(error)
                }), status
        
        if isinstance(result, dict):
            if 'success' not in result:
                result['success'] = True
            return jsonify(result), status
        else:
            return jsonify({
                'success': True,
                'data': result
            }), status

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500