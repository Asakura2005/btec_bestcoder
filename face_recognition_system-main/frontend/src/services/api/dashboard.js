// frontend/src/services/api/dashboard.js

import api from './index'

export const getAdminDashboardStats = () => {
  return api.get('/api/dashboard/admin/stats')
}

export const getAttendanceTrend = (period = 'week') => {
  return api.get('/api/dashboard/admin/trend', { params: { period } })
}

export const getDepartmentSummary = () => {
  return api.get('/api/dashboard/admin/departments')
}

export const getAttendanceHeatmap = (month = null) => {
  const params = {}
  if (month) params.month = month
  return api.get('/api/dashboard/admin/heatmap', { params })
}

export const getEmployeePersonalStats = () => {
  return api.get('/api/dashboard/employee/stats')
}
