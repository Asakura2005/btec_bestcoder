# backend/app/services/dashboard_service.py

from datetime import datetime, timedelta, time
from collections import defaultdict
import pytz
from sqlalchemy import func, and_, case, extract
from app.db import db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.models.settings import Settings
from app.utils.helpers import get_vn_datetime


def _get_vn_today():
    """Lấy ngày hiện tại theo múi giờ VN"""
    vn_tz = pytz.timezone("Asia/Ho_Chi_Minh")
    return datetime.now(vn_tz).date()


def _get_month_range(year=None, month=None):
    """Lấy ngày đầu và cuối tháng"""
    today = _get_vn_today()
    if not year:
        year = today.year
    if not month:
        month = today.month
    
    start = datetime(year, month, 1)
    if month == 12:
        end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        end = datetime(year, month + 1, 1) - timedelta(seconds=1)
    return start, end


def get_admin_dashboard_stats():
    """Thống kê tổng quan cho Admin Dashboard"""
    today = _get_vn_today()
    settings = Settings.get_current_settings()
    
    # Tổng nhân viên active
    total_employees = Employee.query.filter_by(status=True).count()
    
    # Nhân viên đã chấm công hôm nay
    today_checkins = db.session.query(
        func.count(func.distinct(Attendance.employee_id))
    ).filter(
        func.date(Attendance.timestamp) == today,
        Attendance.status == 'check-in'
    ).scalar() or 0
    
    # Nhân viên đi trễ hôm nay
    late_today = db.session.query(
        func.count(func.distinct(Attendance.employee_id))
    ).filter(
        func.date(Attendance.timestamp) == today,
        Attendance.status == 'check-in',
        Attendance.attendance_type == 'late'
    ).scalar() or 0
    
    # Nhân viên đã check-out hôm nay
    checked_out_today = db.session.query(
        func.count(func.distinct(Attendance.employee_id))
    ).filter(
        func.date(Attendance.timestamp) == today,
        Attendance.status == 'check-out'
    ).scalar() or 0
    
    # Vắng mặt = Total - đã check-in
    absent_today = max(0, total_employees - today_checkins)
    
    # Thống kê tháng này
    month_start, month_end = _get_month_range()
    
    # Tổng ngày công tháng này (tất cả NV)
    month_attendances_query = db.session.query(
        Attendance.employee_id, func.date(Attendance.timestamp)
    ).filter(
        Attendance.timestamp >= month_start,
        Attendance.timestamp <= month_end,
        Attendance.status == 'check-in'
    ).all()
    month_attendance_days = len(set(month_attendances_query))
    
    # Late count tháng này
    month_late_count = db.session.query(
        func.count(Attendance.id)
    ).filter(
        Attendance.timestamp >= month_start,
        Attendance.timestamp <= month_end,
        Attendance.status == 'check-in',
        Attendance.attendance_type == 'late'
    ).scalar() or 0
    
    # NV đã training khuôn mặt
    face_trained = Employee.query.filter_by(status=True, face_training_completed=True).count()
    
    return {
        "today": {
            "total_employees": total_employees,
            "present": today_checkins,
            "late": late_today,
            "absent": absent_today,
            "checked_out": checked_out_today,
            "date": today.isoformat()
        },
        "month": {
            "total_attendance_days": month_attendance_days,
            "total_late": month_late_count,
            "month": today.month,
            "year": today.year
        },
        "system": {
            "face_trained": face_trained,
            "face_not_trained": total_employees - face_trained,
            "work_start": settings.start_work.strftime('%H:%M') if settings.start_work else '08:30',
            "work_end": settings.end_work.strftime('%H:%M') if settings.end_work else '17:30'
        }
    }


def get_attendance_trend(period='week'):
    """Thống kê xu hướng chấm công theo ngày"""
    today = _get_vn_today()
    
    if period == 'week':
        days = 7
    elif period == 'month':
        days = 30
    else:
        days = 7
    
    start_date = today - timedelta(days=days - 1)
    total_employees = Employee.query.filter_by(status=True).count()
    
    trend_data = []
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # Skip weekends
        if current_date.weekday() >= 5:
            trend_data.append({
                "date": current_date.isoformat(),
                "day_name": current_date.strftime('%A'),
                "normal": 0,
                "late": 0,
                "half_day": 0,
                "absent": 0,
                "is_weekend": True
            })
            continue
        
        # Query check-in records for this date
        day_records = db.session.query(
            Attendance.attendance_type,
            func.count(func.distinct(Attendance.employee_id))
        ).filter(
            func.date(Attendance.timestamp) == current_date,
            Attendance.status == 'check-in'
        ).group_by(Attendance.attendance_type).all()
        
        counts = {r[0]: r[1] for r in day_records}
        present = sum(counts.values())
        
        trend_data.append({
            "date": current_date.isoformat(),
            "day_name": current_date.strftime('%A'),
            "normal": counts.get('normal', 0),
            "late": counts.get('late', 0),
            "half_day": counts.get('half_day', 0),
            "absent": max(0, total_employees - present),
            "is_weekend": False
        })
    
    return {
        "period": period,
        "days": days,
        "total_employees": total_employees,
        "data": trend_data
    }


def get_department_summary():
    """Thống kê theo phòng ban"""
    today = _get_vn_today()
    
    # Lấy tất cả phòng ban
    departments = db.session.query(
        Employee.department,
        func.count(Employee.id)
    ).filter(
        Employee.status == True,
        Employee.department.isnot(None)
    ).group_by(Employee.department).all()
    
    result = []
    
    for dept_name, total_count in departments:
        # Số người check-in hôm nay trong phòng ban
        present = db.session.query(
            func.count(func.distinct(Attendance.employee_id))
        ).join(Employee, Attendance.employee_id == Employee.employee_id).filter(
            func.date(Attendance.timestamp) == today,
            Attendance.status == 'check-in',
            Employee.department == dept_name,
            Employee.status == True
        ).scalar() or 0
        
        # Số người đi trễ
        late = db.session.query(
            func.count(func.distinct(Attendance.employee_id))
        ).join(Employee, Attendance.employee_id == Employee.employee_id).filter(
            func.date(Attendance.timestamp) == today,
            Attendance.status == 'check-in',
            Attendance.attendance_type == 'late',
            Employee.department == dept_name,
            Employee.status == True
        ).scalar() or 0
        
        result.append({
            "department": dept_name,
            "total": total_count,
            "present": present,
            "absent": max(0, total_count - present),
            "late": late,
            "attendance_rate": round((present / total_count * 100), 1) if total_count > 0 else 0
        })
    
    return result


def get_attendance_heatmap(year=None, month=None):
    """Dữ liệu heatmap: số lượng check-in theo ngày × giờ"""
    start_date, end_date = _get_month_range(year, month)
    
    # Query tất cả check-in records trong tháng
    records = db.session.query(
        func.date(Attendance.timestamp).label('day'),
        extract('hour', Attendance.timestamp).label('hour'),
        func.count(Attendance.id).label('count')
    ).filter(
        Attendance.timestamp >= start_date,
        Attendance.timestamp <= end_date,
        Attendance.status == 'check-in'
    ).group_by(
        func.date(Attendance.timestamp),
        extract('hour', Attendance.timestamp)
    ).all()
    
    # Format cho ApexCharts heatmap
    # Series: mỗi giờ (6-20) là 1 series, data = [{x: ngày, y: count}]
    hours_range = range(6, 21)  # 6AM - 8PM
    
    heatmap_data = []
    for hour in hours_range:
        series = {
            "name": f"{hour:02d}:00",
            "data": []
        }
        
        # Group by date for this hour
        hour_records = {str(r.day): r.count for r in records if int(r.hour) == hour}
        
        current = start_date.date() if hasattr(start_date, 'date') else start_date
        end = end_date.date() if hasattr(end_date, 'date') else end_date
        
        while current <= end:
            if current.weekday() < 5:  # Only weekdays
                series["data"].append({
                    "x": current.strftime('%d/%m'),
                    "y": hour_records.get(str(current), 0)
                })
            current += timedelta(days=1)
        
        heatmap_data.append(series)
    
    return {
        "month": month or _get_vn_today().month,
        "year": year or _get_vn_today().year,
        "series": heatmap_data
    }


def get_employee_personal_stats(employee_id):
    """Thống kê cá nhân cho Employee Dashboard"""
    today = _get_vn_today()
    month_start, month_end = _get_month_range()
    
    employee = Employee.query.filter_by(employee_id=employee_id.upper(), status=True).first()
    if not employee:
        return None
    
    # Ngày công tháng này
    work_days = db.session.query(
        func.count(func.distinct(func.date(Attendance.timestamp)))
    ).filter(
        Attendance.employee_id == employee_id.upper(),
        Attendance.timestamp >= month_start,
        Attendance.timestamp <= month_end,
        Attendance.status == 'check-in'
    ).scalar() or 0
    
    # Số lần đi trễ tháng này
    late_count = db.session.query(
        func.count(Attendance.id)
    ).filter(
        Attendance.employee_id == employee_id.upper(),
        Attendance.timestamp >= month_start,
        Attendance.timestamp <= month_end,
        Attendance.status == 'check-in',
        Attendance.attendance_type == 'late'
    ).scalar() or 0
    
    # Số ngày vắng
    # Tính working days từ đầu tháng đến hôm nay
    working_days = 0
    current = month_start.date() if hasattr(month_start, 'date') else month_start
    while current <= today:
        if current.weekday() < 5:
            working_days += 1
        current += timedelta(days=1)
    
    absent_days = max(0, working_days - work_days)
    
    # Tỷ lệ chuyên cần
    attendance_rate = round((work_days / working_days * 100), 1) if working_days > 0 else 0
    
    # Trạng thái hôm nay
    today_records = Attendance.get_today_records(employee_id=employee_id.upper())
    statuses = [r.status for r in today_records]
    if 'check-in' not in statuses:
        today_status = 'not_checked_in'
    elif 'check-out' not in statuses:
        today_status = 'checked_in'
    else:
        today_status = 'completed'
    
    # Trend 30 ngày gần nhất
    thirty_days_ago = today - timedelta(days=29)
    trend_data = []
    
    for i in range(30):
        d = thirty_days_ago + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        
        record = db.session.query(
            Attendance.attendance_type
        ).filter(
            Attendance.employee_id == employee_id.upper(),
            func.date(Attendance.timestamp) == d,
            Attendance.status == 'check-in'
        ).first()
        
        trend_data.append({
            "date": d.isoformat(),
            "status": record.attendance_type if record else "absent"
        })
    
    return {
        "employee": {
            "employee_id": employee.employee_id,
            "full_name": employee.full_name,
            "department": employee.department,
            "position": employee.position
        },
        "month_stats": {
            "work_days": work_days,
            "late_count": late_count,
            "absent_days": absent_days,
            "attendance_rate": attendance_rate,
            "working_days_total": working_days,
            "month": today.month,
            "year": today.year
        },
        "today_status": today_status,
        "trend": trend_data
    }
