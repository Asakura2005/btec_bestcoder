# backend/app/routes/dashboard_routes.py

from flask import Blueprint, request, jsonify
from app.services.dashboard_service import (
    get_admin_dashboard_stats,
    get_attendance_trend,
    get_department_summary,
    get_attendance_heatmap,
    get_employee_personal_stats
)
from app.utils.decorators import admin_required, employee_required
import logging

dashboard_bp = Blueprint('dashboard', __name__)
logger = logging.getLogger(__name__)


@dashboard_bp.route('/api/dashboard/admin/stats', methods=['GET'])
@admin_required
def admin_stats():
    """Thống kê tổng quan cho Admin"""
    try:
        stats = get_admin_dashboard_stats()
        return jsonify({"success": True, "data": stats}), 200
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route('/api/dashboard/admin/trend', methods=['GET'])
@admin_required
def admin_trend():
    """Xu hướng chấm công theo tuần/tháng"""
    try:
        period = request.args.get('period', 'week')
        if period not in ['week', 'month']:
            return jsonify({"success": False, "error": "Period must be 'week' or 'month'"}), 400
        
        data = get_attendance_trend(period)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Dashboard trend error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route('/api/dashboard/admin/departments', methods=['GET'])
@admin_required
def admin_departments():
    """Thống kê phòng ban"""
    try:
        data = get_department_summary()
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Dashboard departments error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route('/api/dashboard/admin/heatmap', methods=['GET'])
@admin_required
def admin_heatmap():
    """Heatmap chấm công theo giờ"""
    try:
        month_str = request.args.get('month')
        year = None
        month = None
        
        if month_str:
            parts = month_str.split('-')
            if len(parts) == 2:
                year = int(parts[0])
                month = int(parts[1])
        
        data = get_attendance_heatmap(year, month)
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Dashboard heatmap error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@dashboard_bp.route('/api/dashboard/employee/stats', methods=['GET'])
@employee_required
def employee_stats():
    """Thống kê cá nhân cho Employee"""
    try:
        user = request.current_user
        employee_id = user.employee_id
        
        if not employee_id:
            return jsonify({"success": False, "error": "Employee ID not found"}), 400
        
        data = get_employee_personal_stats(employee_id)
        if not data:
            return jsonify({"success": False, "error": "Employee not found"}), 404
        
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        logger.error(f"Employee stats error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500
