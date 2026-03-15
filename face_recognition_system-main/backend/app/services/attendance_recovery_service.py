# app/services/attendance_recovery_service.py
from app.db import db
from app.models.attendance_recovery import AttendanceRecoveryRequest
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.admin import Admin # Import Admin để liên kết người duyệt
from app.utils.helpers import get_vn_datetime, format_datetime_vn # Import format_datetime_vn
from sqlalchemy.exc import IntegrityError
from datetime import datetime, time
from typing import Optional, List, Dict, Any, Tuple       
from app.models.attendance_recovery import AttendanceRecoveryRequest
from app.models.settings import Settings

class AttendanceRecoveryService:
    @staticmethod
    def submit_recovery_request(employee_id: str, request_date_str: str, reason: str) -> Tuple[bool, str]:
        """Nhân viên gửi yêu cầu phục hồi chấm công."""
        employee = Employee.query.filter_by(employee_id=employee_id.upper()).first()
        if not employee:
            return False, "Employee does not exist."

        try:
            request_date = datetime.strptime(request_date_str, '%Y-%m-%d').date()
        except ValueError:
            return False, "Invalid request date. Please use the format YYYY-MM-DD."

        # Kiểm tra xem đã có yêu cầu PENDING hoặc APPROVED cho ngày này chưa
        existing_request = AttendanceRecoveryRequest.query.filter(
            AttendanceRecoveryRequest.employee_id == employee_id.upper(),
            AttendanceRecoveryRequest.request_date == request_date,
            AttendanceRecoveryRequest.status.in_(['pending', 'approved'])
        ).first()

        if existing_request:
            if existing_request.status == 'pending':
                return False, "You already have a pending attendance recovery request for this date."
            elif existing_request.status == 'approved':
                return False, "Attendance recovery for this date has been approved."

        new_request = AttendanceRecoveryRequest(
            employee_id=employee_id.upper(),
            request_date=request_date,
            reason=reason,
            status='pending'
        )
        try:
            db.session.add(new_request)
            db.session.commit()
            return True, "Attendance recovery request submitted successfully."
        except IntegrityError:
            db.session.rollback()
            return False, "Database error when submitting the request. The request may already exist."
        except Exception as e:
            db.session.rollback()
            return False, f"An error occurred while submitting the request: {str(e)}"

    @staticmethod
    def get_employee_recovery_requests(employee_id: str) -> List[Dict[str, Any]]:
        """Lấy danh sách các yêu cầu phục hồi của một nhân viên."""
        requests = AttendanceRecoveryRequest.query.filter_by(employee_id=employee_id.upper()).order_by(
            AttendanceRecoveryRequest.requested_at.desc()
        ).all()
        
        results = []
        for r in requests:
            admin_name = None
            if r.admin_id:
                admin = Admin.query.get(r.admin_id)
                if admin:
                    admin_name = admin.username
            results.append({
                "request_id": r.request_id,
                "employee_id": r.employee_id,
                "request_date": r.request_date.strftime('%Y-%m-%d'),
                "requested_at": format_datetime_vn(r.requested_at),
                "reason": r.reason,
                "status": r.status,
                "admin_username": admin_name, # Tên admin đã duyệt/từ chối
                "approved_at": format_datetime_vn(r.approved_at) if r.approved_at else None,
                "notes": r.notes
            })
        return results

    @staticmethod
    def get_all_pending_recovery_requests() -> List[Dict[str, Any]]:
        """Admin xem tất cả các yêu cầu phục hồi chấm công đang chờ."""
        requests = AttendanceRecoveryRequest.query.filter_by(status='pending')\
            .order_by(AttendanceRecoveryRequest.requested_at.asc())\
            .all()

        return [
            {
                "request_id": r.request_id,
                "employee_id": r.employee.employee_id,
                "employee_name": r.employee.full_name,
                "request_date": r.request_date.strftime('%Y-%m-%d'),
                "requested_at": format_datetime_vn(r.requested_at),
                "reason": r.reason,
                "status": r.status,
            } for r in requests
        ]

    @staticmethod
    def process_recovery_request(request_id: str, admin_id: int, status: str, notes: Optional[str] = None) -> Tuple[bool, str]:
        """Admin duyệt hoặc từ chối yêu cầu phục hồi chấm công."""
        request = AttendanceRecoveryRequest.query.filter_by(request_id=request_id).first()
        if not request:
            return False, "Request not found."
        
        if request.status != 'pending':
            return False, "Request already processed."

        request.status = status
        request.admin_id = admin_id
        request.approved_at = get_vn_datetime()
        request.notes = notes

        try:
            db.session.commit()

            if status == 'approved':
                # Lấy các cài đặt giờ làm việc từ database
                settings = Settings.get_current_settings()
                
                # Sử dụng giờ làm việc từ settings thay vì hard-code
                start_work_time = settings.start_work
                end_work_time = settings.end_work
                
                # Logic để "phục hồi" chấm công trong bảng Attendance
                attendance_records_for_day = Attendance.get_records_by_employee_and_date(
                    employee_id=request.employee_id,
                    target_date=request.request_date
                )

                if not attendance_records_for_day:
                    # Nếu không có bản ghi nào, tạo một bản ghi 'check-in' với type 'recovered'
                    checkin_time = datetime.combine(request.request_date, start_work_time)
                    checkout_time = datetime.combine(request.request_date, end_work_time)
                    
                    # Tạo check-in record
                    checkin_record = Attendance.create_attendance(
                        employee_id=request.employee_id,
                        status='check-in', 
                        timestamp=checkin_time,
                        attendance_type='recovered', 
                        location="Recovery Request", 
                        device_info="System Generated"
                    )
                    db.session.add(checkin_record)
                    
                    # Tạo check-out record để đảm bảo có đủ giờ làm
                    checkout_record = Attendance.create_attendance(
                        employee_id=request.employee_id,
                        status='check-out', 
                        timestamp=checkout_time,
                        attendance_type='recovered', 
                        location="Recovery Request", 
                        device_info="System Generated"
                    )
                    db.session.add(checkout_record)
                else:
                    # Cập nhật tất cả các bản ghi của ngày đó thành 'recovered'
                    for record in attendance_records_for_day:
                        record.attendance_type = 'recovered'
                        
                db.session.commit()

            return True, f"The request has been {status}."
        except IntegrityError:
            db.session.rollback()
            return False, "Database error while processing the request."
        except Exception as e:
            db.session.rollback()
            return False, f"An error occurred: {str(e)}"

    @staticmethod
    def get_all_recovery_requests() -> List[Dict[str, Any]]:
        """Admin xem tất cả các yêu cầu phục hồi chấm công (bao gồm pending, approved, rejected)."""
        requests = AttendanceRecoveryRequest.query\
            .order_by(AttendanceRecoveryRequest.requested_at.desc())\
            .all()

        results = []
        for r in requests:
            admin_name = None
            if r.admin_id:
                admin = Admin.query.get(r.admin_id)
                if admin:
                    admin_name = admin.username
            
            results.append({
                "request_id": r.request_id,
                "employee_id": r.employee.employee_id,
                "employee_name": r.employee.full_name,
                "request_date": r.request_date.strftime('%Y-%m-%d'),
                "requested_at": format_datetime_vn(r.requested_at),
                "reason": r.reason,
                "status": r.status,
                "admin_username": admin_name,  # Tên admin đã duyệt/từ chối
                "approved_at": format_datetime_vn(r.approved_at) if r.approved_at else None,
                "notes": r.notes
            })
        return results