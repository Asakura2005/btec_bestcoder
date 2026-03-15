# app/models/settings.py

from app import db
from datetime import time

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Time Configuration (aligned with frontend)
    enable_time_management = db.Column(db.Boolean, default=True)
    start_work = db.Column(db.Time, default=time(8, 30))
    end_work = db.Column(db.Time, default=time(17, 30))
    checkin_start_window = db.Column(db.Time, default=time(7, 0))
    checkin_end_window = db.Column(db.Time, default=time(9, 0))
    lunch_start = db.Column(db.Time, default=time(12, 0))
    lunch_end = db.Column(db.Time, default=time(13, 30))
    minimum_work_hours = db.Column(db.Float, default=4.0)
    
    # Original time settings
    enable_time_validation = db.Column(db.Boolean, default=True)
    allow_weekend_work = db.Column(db.Boolean, default=True)
    auto_break_deduction = db.Column(db.Boolean, default=True)
    allow_early_checkout = db.Column(db.Boolean, default=False)
    strict_time_enforcement = db.Column(db.Boolean, default=False)

    # Policy Settings
    enable_policies = db.Column(db.Boolean, default=True)
    max_checkins_per_day = db.Column(db.Integer, default=1)
    max_checkouts_per_day = db.Column(db.Integer, default=1)
    late_arrival_grace_period_minutes = db.Column(db.Integer, default=15)
    overtime_threshold_hours = db.Column(db.Float, default=8.0)

    # Notification Settings
    enable_notifications = db.Column(db.Boolean, default=True)
    enable_admin_alerts = db.Column(db.Boolean, default=True)
    enable_employee_reminders = db.Column(db.Boolean, default=True)
    enable_system_health_monitoring = db.Column(db.Boolean, default=True)
    enable_daily_reports = db.Column(db.Boolean, default=False)
    
    # Original notification settings
    enable_email_notifications = db.Column(db.Boolean, default=False)
    enable_late_arrival_alert = db.Column(db.Boolean, default=True)
    enable_absentee_alert = db.Column(db.Boolean, default=True)
    enable_overtime_notifications = db.Column(db.Boolean, default=True)
    absentee_alert_delay = db.Column(db.Float, default=2.0)

    # Security Settings
    enable_security = db.Column(db.Boolean, default=True)
    data_retention_days = db.Column(db.Integer, default=365)
    session_timeout = db.Column(db.Integer, default=60)
    backup_frequency = db.Column(db.String(50), default='daily')
    enable_audit_log = db.Column(db.Boolean, default=True)  # THÊM FIELD NÀY

    # Device & Location Settings
    enable_device_location = db.Column(db.Boolean, default=True)
    enable_location_tracking = db.Column(db.Boolean, default=False)
    enable_camera_quality_check = db.Column(db.Boolean, default=True)
    enable_device_registration = db.Column(db.Boolean, default=False)
    minimum_image_resolution = db.Column(db.String(50), default='720p')
    image_quality_threshold = db.Column(db.Float, default=0.7)
    
    # Face Recognition Settings
    confidence_threshold = db.Column(db.Float, default=0.75)
    enable_liveness_detection = db.Column(db.Boolean, default=True)
    enable_multiple_face_check = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Chuyển đổi đối tượng Settings thành dictionary để trả về cho frontend"""
        return {
            "timeSettings": {
                "enabled": self.enable_time_management,
                "workStartTime": self.start_work.strftime('%H:%M') if self.start_work else None,
                "workEndTime": self.end_work.strftime('%H:%M') if self.end_work else None,
                "checkinStart": self.checkin_start_window.strftime('%H:%M') if self.checkin_start_window else None,
                "checkinEnd": self.checkin_end_window.strftime('%H:%M') if self.checkin_end_window else None,
                "lunchStart": self.lunch_start.strftime('%H:%M') if self.lunch_start else None,
                "lunchEnd": self.lunch_end.strftime('%H:%M') if self.lunch_end else None,
                "minWorkHours": self.minimum_work_hours,
                "enableTimeValidation": self.enable_time_validation,
                "allowWeekendWork": self.allow_weekend_work,
                "autoBreakDeduction": self.auto_break_deduction,
                "allowEarlyCheckout": self.allow_early_checkout,
                "strictTimeEnforcement": self.strict_time_enforcement
            },
            "policySettings": {
                "enabled": self.enable_policies,
                "maxCheckins": self.max_checkins_per_day,
                "maxCheckouts": self.max_checkouts_per_day,
                "gracePeriod": self.late_arrival_grace_period_minutes,
                "overtimeThreshold": self.overtime_threshold_hours
            },
            "notificationSettings": {
                "enabled": self.enable_notifications,
                "adminAlerts": self.enable_admin_alerts,
                "employeeReminders": self.enable_employee_reminders,
                "systemHealth": self.enable_system_health_monitoring,
                "dailyReports": self.enable_daily_reports,
                "enableEmailNotifications": self.enable_email_notifications,
                "enableLateArrivalAlert": self.enable_late_arrival_alert,
                "enableAbsenteeAlert": self.enable_absentee_alert,
                "enableOvertimeNotifications": self.enable_overtime_notifications,
                "absenteeAlertDelay": self.absentee_alert_delay
            },
            "securitySettings": {
                "enabled": self.enable_security,
                "dataRetentionDays": self.data_retention_days,
                "sessionTimeout": self.session_timeout,
                "backupFrequency": self.backup_frequency,
                "enableAuditLog": self.enable_audit_log
            },
            "deviceSettings": {
                "enabled": self.enable_device_location,
                "locationRestrictions": self.enable_location_tracking,
                "cameraQualityCheck": self.enable_camera_quality_check,
                "deviceRegistration": self.enable_device_registration,
                "minResolution": self.minimum_image_resolution,
                "imageQualityThreshold": self.image_quality_threshold,
                "enableLivenessDetection": self.enable_liveness_detection,
                "enableMultipleFaceCheck": self.enable_multiple_face_check
            },
            "faceSettings": {
                "confidenceThreshold": self.confidence_threshold,
            }
        }

    @classmethod
    def get_current_settings(cls):
        """Lấy cài đặt hiện tại, nếu chưa có thì tạo mới với giá trị mặc định"""
        settings = cls.query.first()
        if not settings:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

    def update_from_dict(self, data):
        """Cập nhật các trường từ dictionary"""
        from datetime import time
        def parse_time(value, field_name):
            try:
                if value is None or value == '':
                    return None
                return time.fromisoformat(value)
            except ValueError:
                raise ValueError(f"Invalid time format for {field_name}")

        # Time Configuration
        if 'timeSettings' in data:
            ts = data['timeSettings']
            self.enable_time_management = ts.get('enabled', self.enable_time_management)
            self.start_work = parse_time(ts.get('workStartTime'), 'workStartTime')
            self.end_work = parse_time(ts.get('workEndTime'), 'workEndTime')
            self.checkin_start_window = parse_time(ts.get('checkinStart'), 'checkinStart')
            self.checkin_end_window = parse_time(ts.get('checkinEnd'), 'checkinEnd')
            self.lunch_start = parse_time(ts.get('lunchStart'), 'lunchStart')
            self.lunch_end = parse_time(ts.get('lunchEnd'), 'lunchEnd')
            self.minimum_work_hours = ts.get('minWorkHours', self.minimum_work_hours)
            if self.minimum_work_hours is not None and self.minimum_work_hours < 1:
                raise ValueError("Minimum work hours must be at least 1")
            
            self.enable_time_validation = ts.get('enableTimeValidation', self.enable_time_validation)
            self.allow_weekend_work = ts.get('allowWeekendWork', self.allow_weekend_work)
            self.auto_break_deduction = ts.get('autoBreakDeduction', self.auto_break_deduction)
            self.allow_early_checkout = ts.get('allowEarlyCheckout', self.allow_early_checkout)
            self.strict_time_enforcement = ts.get('strictTimeEnforcement', self.strict_time_enforcement)

            # Validate time order
            times = [t for t in [self.checkin_start_window, self.start_work, self.checkin_end_window] if t is not None]
            if len(times) >= 2:
                sorted_times = sorted(times)
                if not all(sorted_times[i] == times[i] for i in range(len(times))):
                     raise ValueError("Invalid time order: check-in window and work start time must be sequential.")
            if self.start_work and self.end_work and self.start_work >= self.end_work:
                raise ValueError("Invalid work time: start_work must be before end_work")
            if self.lunch_start and self.lunch_end and self.lunch_start >= self.lunch_end:
                raise ValueError("Invalid lunch time: lunch_start must be before lunch_end")

        # Policy Settings
        if 'policySettings' in data:
            ps = data['policySettings']
            self.enable_policies = ps.get('enabled', self.enable_policies)
            self.max_checkins_per_day = ps.get('maxCheckins', self.max_checkins_per_day)
            if self.max_checkins_per_day < 1: raise ValueError("Max check-ins must be at least 1")
            self.max_checkouts_per_day = ps.get('maxCheckouts', self.max_checkouts_per_day)
            if self.max_checkouts_per_day < 1: raise ValueError("Max check-outs must be at least 1")
            self.late_arrival_grace_period_minutes = ps.get('gracePeriod', self.late_arrival_grace_period_minutes)
            if self.late_arrival_grace_period_minutes < 0: raise ValueError("Grace period cannot be negative")
            self.overtime_threshold_hours = ps.get('overtimeThreshold', self.overtime_threshold_hours)
            if self.overtime_threshold_hours < 0: raise ValueError("Overtime threshold cannot be negative")

        # Notification Settings
        if 'notificationSettings' in data:
            ns = data['notificationSettings']
            self.enable_notifications = ns.get('enabled', self.enable_notifications)
            self.enable_admin_alerts = ns.get('adminAlerts', self.enable_admin_alerts)
            self.enable_employee_reminders = ns.get('employeeReminders', self.enable_employee_reminders)
            self.enable_system_health_monitoring = ns.get('systemHealth', self.enable_system_health_monitoring)
            self.enable_daily_reports = ns.get('dailyReports', self.enable_daily_reports)
            
            self.enable_email_notifications = ns.get('enableEmailNotifications', self.enable_email_notifications)
            self.enable_late_arrival_alert = ns.get('enableLateArrivalAlert', self.enable_late_arrival_alert)
            self.enable_absentee_alert = ns.get('enableAbsenteeAlert', self.enable_absentee_alert)
            self.enable_overtime_notifications = ns.get('enableOvertimeNotifications', self.enable_overtime_notifications)
            self.absentee_alert_delay = ns.get('absenteeAlertDelay', self.absentee_alert_delay)

        # Security Settings
        if 'securitySettings' in data:
            ss = data['securitySettings']
            self.enable_security = ss.get('enabled', self.enable_security)
            self.data_retention_days = ss.get('dataRetentionDays', self.data_retention_days)
            if self.data_retention_days is not None and self.data_retention_days < 0: 
                raise ValueError("Data retention days cannot be negative")
            self.session_timeout = ss.get('sessionTimeout', self.session_timeout)
            if self.session_timeout is not None and self.session_timeout < 0: 
                raise ValueError("Session timeout cannot be negative")
            self.backup_frequency = ss.get('backupFrequency', self.backup_frequency)
            self.enable_audit_log = ss.get('enableAuditLog', self.enable_audit_log)

        # Device & Location Settings
        if 'deviceSettings' in data:
            ds = data['deviceSettings']
            self.enable_device_location = ds.get('enabled', self.enable_device_location)
            self.enable_location_tracking = ds.get('locationRestrictions', self.enable_location_tracking)
            self.enable_camera_quality_check = ds.get('cameraQualityCheck', self.enable_camera_quality_check)
            self.enable_device_registration = ds.get('deviceRegistration', self.enable_device_registration)
            self.minimum_image_resolution = ds.get('minResolution', self.minimum_image_resolution)
            self.image_quality_threshold = ds.get('imageQualityThreshold', self.image_quality_threshold)
            if self.image_quality_threshold is not None and not (0.0 <= self.image_quality_threshold <= 1.0):
                raise ValueError("Image quality threshold must be between 0.0 and 1.0")

            self.enable_liveness_detection = ds.get('enableLivenessDetection', self.enable_liveness_detection)
            self.enable_multiple_face_check = ds.get('enableMultipleFaceCheck', self.enable_multiple_face_check)
        
        # Face Recognition Settings
        if 'faceSettings' in data:
            fs = data['faceSettings']
            self.confidence_threshold = fs.get('confidenceThreshold', self.confidence_threshold)
            if self.confidence_threshold is not None and not (0.0 <= self.confidence_threshold <= 1.0):
                raise ValueError("Confidence threshold must be between 0.0 and 1.0")

        db.session.commit()