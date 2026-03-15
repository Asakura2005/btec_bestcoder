from flask import Blueprint, request, jsonify, send_file
from app.services.report_service import (
    get_date_range, 
    get_employee_report_enhanced, 
    get_department_report_enhanced, 
    export_to_excel_enhanced,
    get_company_settings  # THAY ĐỔI: import function mới thay vì COMPANY_CONFIG
)
from app.utils.helpers import get_export_path
from app.utils.decorators import employee_required, admin_required
import os
import logging

# Khởi tạo Blueprint và logging
report_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)

@report_bp.route('/api/reports/employee/<string:employee_id>', methods=['GET'])
@admin_required
def employee_report(employee_id):
    """Báo cáo chấm công nâng cao của một nhân viên"""
    start_date, end_date, error, status = get_date_range(request.args)
    if error:
        return jsonify(error), status
    
    result, error, status = get_employee_report_enhanced(employee_id, start_date, end_date)
    if error:
        return jsonify(error), status
    return jsonify(result), 200

@report_bp.route('/api/reports/department/<string:department>', methods=['GET'])
@admin_required
def department_report(department):
    """Báo cáo chấm công nâng cao của một phòng ban"""
    start_date, end_date, error, status = get_date_range(request.args)
    if error:
        return jsonify(error), status
    
    result, error, status = get_department_report_enhanced(department, start_date, end_date)
    if error:
        return jsonify(error), status
    return jsonify(result), 200

@report_bp.route('/api/reports/export/<path:report_type>', methods=['GET'])
@admin_required
def export_report(report_type):
    """Xuất báo cáo nâng cao ra file Excel"""
    try:
        # Validate report_type format
        if not report_type or '/' not in report_type:
            return jsonify({"error": "Invalid report type format. Use 'employee/{id}' or 'department/{name}'"}), 400
        
        start_date, end_date, error, status = get_date_range(request.args)
        if error:
            return jsonify(error), status
        
        result, error, status = export_to_excel_enhanced(report_type, start_date, end_date)
        if error:
            return jsonify(error), status
        
        # Kiểm tra file tồn tại
        file_path = result.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Export file not found"}), 404
        
        # Trả về file hoặc thông tin
        download_direct = request.args.get('download', 'false').lower() == 'true'
        
        if download_direct:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=result['filename'],
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
        else:
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return jsonify({"error": f"Export failed: {str(e)}"}), 500

@report_bp.route('/api/reports/download/<filename>', methods=['GET'])
@admin_required
def download_exported_file(filename):
    """Download file đã export"""
    try:
        export_path = get_export_path()
        file_path = os.path.join(export_path, filename)
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@report_bp.route('/api/reports/company-config', methods=['GET'])
@admin_required
def get_company_config_route():  # THAY ĐỔI: đổi tên function để tránh conflict
    """Lấy cấu hình quy định công ty"""
    try:
        # THAY ĐỔI: Gọi function thay vì dùng constant
        company_config = get_company_settings()
        
        # Chuyển đổi time objects thành string
        config = {}
        for key, value in company_config.items():
            if hasattr(value, 'strftime'):
                config[key] = value.strftime('%H:%M')
            else:
                config[key] = value
        
        return jsonify({
            "config": config,
            "message": "Company configuration retrieved successfully"
        }), 200
        
    except Exception as e:
        logger.error(f"Config error: {str(e)}")
        return jsonify({"error": f"Failed to get config: {str(e)}"}), 500

@report_bp.route('/api/reports/export-status', methods=['GET'])
@admin_required
def export_status():
    """Kiểm tra trạng thái export và danh sách file"""
    try:
        export_path = get_export_path()
        
        if not os.path.exists(export_path):
            return jsonify({"message": "Export directory not found", "files": []}), 200
        
        files = []
        for filename in os.listdir(export_path):
            if filename.endswith('.xlsx'):
                file_path = os.path.join(export_path, filename)
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created": stat.st_mtime,
                    "download_url": f"/api/reports/download/{filename}"
                })
        
        return jsonify({
            "message": "Export status retrieved successfully",
            "export_path": export_path,
            "files": files
        }), 200
        
    except Exception as e:
        logger.error(f"Export status error: {str(e)}")
        return jsonify({"error": f"Failed to get export status: {str(e)}"}), 500