# backend/app/routes/payroll_routes.py

from flask import Blueprint, request, jsonify
from app.services.payroll_service import (
    calculate_employee_salary,
    generate_payroll_batch,
    get_payroll_list,
    export_payroll_excel
)
from app.models.payroll import PayrollConfig
from app.utils.decorators import admin_required
from app.db import db
import logging

payroll_bp = Blueprint('payroll', __name__)
logger = logging.getLogger(__name__)


@payroll_bp.route('/api/payroll/calculate/<string:employee_id>', methods=['GET'])
@admin_required
def calculate_salary(employee_id):
    """Tính lương cho 1 nhân viên"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({"success": False, "error": "Month and year are required"}), 400
        if month < 1 or month > 12:
            return jsonify({"success": False, "error": "Invalid month"}), 400
        
        result, error = calculate_employee_salary(employee_id, month, year)
        if error:
            return jsonify({"success": False, "error": error}), 404
        
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"Calculate salary error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@payroll_bp.route('/api/payroll/generate', methods=['POST'])
@admin_required
def generate_payroll():
    """Tạo bảng lương cho tất cả NV"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({"success": False, "error": "Month and year are required"}), 400
        
        result, error = generate_payroll_batch(month, year)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"Generate payroll error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@payroll_bp.route('/api/payroll/list', methods=['GET'])
@admin_required
def list_payroll():
    """Danh sách lương tháng"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({"success": False, "error": "Month and year are required"}), 400
        
        result = get_payroll_list(month, year)
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"List payroll error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@payroll_bp.route('/api/payroll/config', methods=['GET'])
@admin_required
def get_config():
    """Lấy cấu hình lương"""
    try:
        config = PayrollConfig.get_current()
        return jsonify({"success": True, "data": config.to_dict()}), 200
    except Exception as e:
        logger.error(f"Get payroll config error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@payroll_bp.route('/api/payroll/config', methods=['PUT'])
@admin_required
def update_config():
    """Cập nhật cấu hình lương"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        config = PayrollConfig.get_current()
        
        if 'base_salary' in data:
            if data['base_salary'] <= 0:
                return jsonify({"success": False, "error": "Base salary must be positive"}), 400
            config.base_salary = data['base_salary']
        if 'ot_multiplier' in data:
            if data['ot_multiplier'] < 1:
                return jsonify({"success": False, "error": "OT multiplier must be >= 1"}), 400
            config.ot_multiplier = data['ot_multiplier']
        if 'late_deduction' in data:
            if data['late_deduction'] < 0:
                return jsonify({"success": False, "error": "Late deduction cannot be negative"}), 400
            config.late_deduction = data['late_deduction']
        if 'absent_deduction_rate' in data:
            if data['absent_deduction_rate'] < 0:
                return jsonify({"success": False, "error": "Absent deduction rate cannot be negative"}), 400
            config.absent_deduction_rate = data['absent_deduction_rate']
        if 'working_days_per_month' in data:
            if data['working_days_per_month'] < 1 or data['working_days_per_month'] > 31:
                return jsonify({"success": False, "error": "Working days must be 1-31"}), 400
            config.working_days_per_month = data['working_days_per_month']
        
        db.session.commit()
        return jsonify({"success": True, "data": config.to_dict(), "message": "Config updated"}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Update payroll config error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@payroll_bp.route('/api/payroll/export', methods=['GET'])
@admin_required
def export_payroll():
    """Xuất bảng lương Excel"""
    try:
        month = request.args.get('month', type=int)
        year = request.args.get('year', type=int)
        
        if not month or not year:
            return jsonify({"success": False, "error": "Month and year are required"}), 400
        
        result, error = export_payroll_excel(month, year)
        if error:
            return jsonify({"success": False, "error": error}), 400
        
        return jsonify({"success": True, "data": result}), 200
    except Exception as e:
        logger.error(f"Export payroll error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
