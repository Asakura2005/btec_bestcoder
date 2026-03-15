// src/services/api/employees.js
import api from './index'

// Thêm nhân viên mới
export const addEmployee = async (formData) => {
  try {
    console.log('👤 Add employee request')
    
    const response = await api.post('/api/employees', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    
    console.log('Add employee success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Add employee error:', error.response?.data || error.message)
    throw error
  }
}

// Lấy danh sách nhân viên
export const getEmployees = async (params = {}) => {
  try {
    console.log('👥 Get employees:', params)
    
    const response = await api.get('/api/employees', { params })
    
    console.log('Get employees success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Get employees error:', error.response?.data || error.message)
    throw error
  }
}

// Lấy chi tiết một nhân viên
export const getEmployeeDetail = async (employee_id) => {
  try {
    console.log('Get employee detail:', employee_id)
    
    const response = await api.get(`/api/employees/${employee_id}`)
    
    console.log('Get employee detail success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Get employee detail error:', error.response?.data || error.message)
    throw error
  }
}

// Cập nhật thông tin nhân viên
export const updateEmployee = async (employee_id, formData) => {
  try {
    console.log('Update employee request:', employee_id)
    
    const response = await api.put(`/api/employees/${employee_id}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    
    console.log('Update employee success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Update employee error:', error.response?.data || error.message)
    throw error
  }
}

// Xóa mềm nhân viên
export const deleteEmployee = async (employee_id) => {
  try {
    console.log('Delete employee request:', employee_id)
    
    const response = await api.delete(`/api/employees/${employee_id}`)
    
    console.log('Delete employee success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Delete employee error:', error.response?.data || error.message)
    throw error
  }
}

// Khôi phục nhân viên
export const restoreEmployee = async (employee_id) => {
  try {
    console.log('Restore employee request:', employee_id)
    
    const response = await api.put(`/api/employees/${employee_id}/restore`)
    
    console.log('Restore employee success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Restore employee error:', error.response?.data || error.message)
    throw error
  }
}

// Đặt lại mật khẩu cho nhân viên (Admin)
export const setEmployeePassword = async (employee_id, new_password, username = null) => {
  try {
    console.log('Set employee password request:', employee_id)
    const payload = { new_password };
    if (username) {
      payload.username = username;
    }
    const response = await api.post(`/api/employees/${employee_id}/set-password`, payload)
    console.log('Set employee password success:', response.data)
    return response.data
  } catch (error) {
    console.error('Set employee password error:', error.response?.data || error.message)
    throw error
  }
}

// Nhân viên đổi mật khẩu
export const employeeChangePassword = async (oldPassword, newPassword, confirmNewPassword) => {
  try {
    const response = await api.post('/api/employee/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
      confirm_new_password: confirmNewPassword,
    });
    return response.data;
  } catch (error) {
    console.error('Employee change password error:', error.response?.data || error.message);
    throw error;
  }
};