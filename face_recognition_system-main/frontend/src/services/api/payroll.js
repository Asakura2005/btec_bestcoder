// frontend/src/services/api/payroll.js

import api from './index'

export const calculateSalary = (employeeId, month, year) => {
  return api.get(`/api/payroll/calculate/${employeeId}`, { params: { month, year } })
}

export const generatePayroll = (month, year) => {
  return api.post(`/api/payroll/generate?month=${month}&year=${year}`)
}

export const getPayrollList = (month, year) => {
  return api.get('/api/payroll/list', { params: { month, year } })
}

export const getPayrollConfig = () => {
  return api.get('/api/payroll/config')
}

export const updatePayrollConfig = (data) => {
  return api.put('/api/payroll/config', data)
}

export const exportPayroll = (month, year) => {
  return api.get('/api/payroll/export', { params: { month, year } })
}
