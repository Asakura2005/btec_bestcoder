# app/routes/attendance_recovery_routes.py
from flask import Blueprint, request, jsonify
from app.services.attendance_recovery_service import AttendanceRecoveryService
from app.utils.decorators import employee_required, admin_required
from app.services.report_service import get_date_range, get_employee_report_enhanced
from datetime import datetime

attendance_recovery_bp = Blueprint('attendance_recovery_bp', __name__)

# --- ROUTES CHO NHÂN VIÊN ---

@attendance_recovery_bp.route('/api/employee/attendance/recovery/submit', methods=['POST'])
@employee_required # Chỉ nhân viên đã đăng nhập mới được gửi yêu cầu
def submit_employee_recovery_request():
    data = request.get_json(silent=True) or {}
    request_date = data.get('request_date') # Định dạng YYYY-MM-DD
    reason = data.get('reason')
    
    # request.current_user được đặt bởi decorator @employee_required
    current_employee_id = request.current_user.employee_id 

    if not request_date or not reason:
        return jsonify({"error": "Date and recovery reason are required."}), 400

    success, message = AttendanceRecoveryService.submit_recovery_request(
        current_employee_id, request_date, reason
    )
    if not success:
        return jsonify({"error": message}), 400
    return jsonify({"message": message}), 201

@attendance_recovery_bp.route('/api/employee/attendance/recovery/my-requests', methods=['GET'])
@employee_required # Chỉ nhân viên đã đăng nhập mới được xem yêu cầu của mình
def get_my_recovery_requests():
    current_employee_id = request.current_user.employee_id
    requests = AttendanceRecoveryService.get_employee_recovery_requests(current_employee_id)
    return jsonify({"requests": requests}), 200


@attendance_recovery_bp.route('/api/employee/attendance/history', methods=['GET'])
@employee_required # CHỈ NHÂN VIÊN ĐÃ ĐĂNG NHẬP MỚI ĐƯỢC XEM LỊCH SỬ CỦA CHÍNH HỌ
def get_current_employee_attendance_history():
    """Lấy lịch sử chấm công của nhân viên đang đăng nhập."""
    current_employee_id = request.current_user.employee_id # Lấy employee_id từ token đã xác thực

    start_date, end_date, error, status = get_date_range(request.args)
    if error:
        return jsonify(error), status
    
    result, error, status = get_employee_report_enhanced(current_employee_id, start_date, end_date)
    if error:
        return jsonify(error), status
    return jsonify(result), 200


# --- ROUTES CHO ADMIN ---

# Thêm route mới để lấy tất cả requests
@attendance_recovery_bp.route('/api/admin/attendance/recovery/all', methods=['GET'])
@admin_required
def get_all_recovery_requests():
    requests = AttendanceRecoveryService.get_all_recovery_requests()
    return jsonify({"requests": requests}), 200

@attendance_recovery_bp.route('/api/admin/attendance/recovery/pending', methods=['GET'])
@admin_required # Chỉ Admin mới được xem các yêu cầu đang chờ
def get_pending_recovery_requests():
    requests = AttendanceRecoveryService.get_all_pending_recovery_requests()
    return jsonify({"pending_requests": requests}), 200

@attendance_recovery_bp.route('/api/admin/attendance/recovery/process/<string:request_id>', methods=['POST'])
@admin_required  # Gắn request.current_user
def process_attendance_recovery(request_id):
    data = request.get_json(silent=True) or {}
    status = data.get('status')  # 'approved' hoặc 'rejected'
    notes = data.get('notes')

    admin = getattr(request, "current_user", None)
    if not admin:
        return jsonify({"error": "Admin not authenticated. Please log in again."}), 401
    
    if status not in ['approved', 'rejected']:
        return jsonify({"error": "Invalid status. Only 'approved' or 'rejected' are accepted."}), 400

    success, message = AttendanceRecoveryService.process_recovery_request(
        request_id=request_id,
        admin_id=admin.id,
        status=status,
        notes=notes
    )

    if not success:
        return jsonify({"error": message}), 400
    return jsonify({"message": message}), 200
