// src/services/api/attendance.js
import api from './index'

// Lấy lịch sử chấm công của một nhân viên (Admin dùng)
export const getAttendanceHistory = async (employee_id) => {
  try {
    console.log('Get attendance history:', employee_id)
    const response = await api.get(`/api/attendance/${employee_id}`)
    return response.data
  } catch (error) {
    console.error('Get attendance history error:', error.response?.data || error.message)
    throw error
  }
}

// Lấy lịch sử chấm công của nhân viên đang đăng nhập
export const getMyAttendanceHistory = async (params = {}) => {
  try {
    console.log('Get my attendance history:', params)
    const response = await api.get('/api/employee/attendance/history', { params })
    return response.data
  } catch (error) {
    console.error('Get my attendance history error:', error.response?.data || error.message)
    throw error
  }
}

// Lấy chấm công hôm nay của một nhân viên
export const getTodayAttendance = async (employee_id) => {
  try {
    console.log('Get today attendance:', employee_id)
    const response = await api.get(`/api/attendance/today/${employee_id}`)
    return response.data
  } catch (error) {
    console.error('Get today attendance error:', error.response?.data || error.message)
    throw error
  }
}
