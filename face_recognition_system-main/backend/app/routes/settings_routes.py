from flask import Blueprint, request, jsonify
from app.models.settings import Settings
from app.models.attendance import Attendance
from app.models.face_training_data import FaceTrainingData
from app.models.employee import Employee
from app.models.admin import Admin
from app.utils.decorators import admin_required
from app import db
from datetime import datetime, timedelta
import os
import shutil

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/api/settings', methods=['GET'])
@admin_required
def get_settings():
    """Lấy tất cả các cài đặt hiện có."""
    settings = Settings.get_current_settings()
    return jsonify(settings.to_dict()), 200

@settings_bp.route('/api/settings', methods=['POST'])
@admin_required
def update_settings():
    """Cập nhật các cài đặt."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid or missing JSON data"}), 400

    settings = Settings.get_current_settings()
    try:
        settings.update_from_dict(data)
        db.session.commit()
        return jsonify({"message": "Settings updated successfully", "settings": settings.to_dict()}), 200
    except ValueError as ve:
        return jsonify({"error": f"Validation error: {str(ve)}"}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Error updating settings: {e}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@settings_bp.route('/api/settings/cleanup-data', methods=['POST'])
@admin_required
def cleanup_old_data():
    """Xóa dữ liệu cũ dựa trên cài đặt Data Retention Days."""
    settings = Settings.get_current_settings()
    data_retention_days = settings.data_retention_days

    if data_retention_days is None or data_retention_days <= 0:
        return jsonify({"message": "Data retention not configured or disabled"}), 200

    try:
        cutoff_date = datetime.now() - timedelta(days=data_retention_days)
        records_to_delete = Attendance.query.filter(Attendance.timestamp < cutoff_date).all()
        
        deleted_count = 0
        for record in records_to_delete:
            db.session.delete(record)
            deleted_count += 1
        
        db.session.commit()
        return jsonify({"message": f"Successfully cleaned up {deleted_count} old attendance records."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error cleaning up data: {e}")
        return jsonify({"error": f"Failed to cleanup data: {str(e)}"}), 500

@settings_bp.route('/api/settings/create-backup', methods=['POST'])
@admin_required
def create_backup():
    """Tạo bản sao lưu cơ sở dữ liệu."""
    try:
        db_path = db.engine.url.database
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        backup_filename = f"database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        if not os.access(backup_dir, os.W_OK):
            return jsonify({"error": "No write permission for backup directory"}), 500
        
        if os.path.exists(db_path):
            shutil.copyfile(db_path, backup_path)
            return jsonify({"message": f"Database backup created at {backup_path}"}), 200
        else:
            return jsonify({"error": "Database file not found"}), 500
    except Exception as e:
        print(f"Error creating backup: {e}")
        return jsonify({"error": f"Failed to create backup: {str(e)}"}), 500

@settings_bp.route('/api/settings/reset-system', methods=['POST'])
@admin_required
def reset_system():
    """Đặt lại tất cả các cài đặt về giá trị mặc định và xóa dữ liệu."""
    try:
        db.session.query(Settings).delete()
        default_settings = Settings()
        db.session.add(default_settings)

        db.session.query(Attendance).delete()
        db.session.query(FaceTrainingData).delete()
        db.session.query(Employee).update({Employee.face_training_status: 'pending'})

        db.session.commit()
        
        return jsonify({"message": "System reset successfully to default settings and data cleared."}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting system: {e}")
        return jsonify({"error": f"Failed to reset system: {str(e)}"}), 500
