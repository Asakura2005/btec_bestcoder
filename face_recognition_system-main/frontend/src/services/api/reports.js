// src/services/api/reports.js
import api from './index'

// Lấy báo cáo theo nhân viên
export const getEmployeeReport = async (employee_id, startDate, endDate) => {
  try {
    console.log('Get employee report:', employee_id, startDate, endDate)
    const response = await api.get(`/api/reports/employee/${employee_id}`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  } catch (error) {
    console.error('Get employee report error:', error.response?.data || error.message)
    throw error
  }
}

// Lấy báo cáo theo phòng ban
export const getDepartmentReport = async (department, startDate, endDate) => {
  try {
    console.log('Get department report:', department, startDate, endDate)
    const response = await api.get(`/api/reports/department/${department}`, {
      params: { start_date: startDate, end_date: endDate }
    })
    return response.data
  } catch (error) {
    console.error('Get department report error:', error.response?.data || error.message)
    throw error
  }
}

// Xuất báo cáo
export const exportReport = async (reportType, startDate, endDate) => {
  try {
    console.log('Export report request:', reportType, startDate, endDate)
    const response = await api.get(`/api/reports/export/${reportType}`, {
      params: {
        start_date: startDate,
        end_date: endDate,
        download: true
      },
      responseType: 'blob'
    })
    return response.data
  } catch (error) {
    console.error('Export report error:', error.response?.data || error.message)
    throw error
  }
}

// Utility function để download file
export const downloadReportFile = (blob, filename) => {
  try {
    console.log('Download report file:', filename)
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    console.log('Download file success:', filename)
    return true
    
  } catch (error) {
    console.error('Download file error:', error)
    throw error
  }
}

// Helper function để format report type
export const formatReportType = (type, id) => {
  switch (type) {
    case 'employee':
      return `employee/${id}`
    case 'department':
      return `department/${id}`
    default:
      return type
  }
}

// Helper function để parse company config
export const parseCompanyConfig = (config) => {
  const parsed = {}
  
  for (const [key, value] of Object.entries(config)) {
    if (typeof value === 'string' && value.includes(':')) {
      parsed[key] = value
    } else {
      parsed[key] = value
    }
  }
  return parsed
}