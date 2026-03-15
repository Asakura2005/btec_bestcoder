// src/services/api/auth.js
import api from './index'

// Admin login
export const login = async (username, password) => {
  try {
    console.log('Admin Login request:', { username: username.trim() })
    
    const response = await api.post('/api/auth/admin/login', {
      username: username.trim(), 
      password: password.trim() 
    })
    
    console.log('Admin Login success:', {
      hasToken: !!response.data.token,
      user: response.data.username
    })
    
    return response.data
    
  } catch (error) {
    console.error('Admin Login error:', error.response?.data || error.message)
    throw error
  }
}

// Employee login
export const loginEmployee = async (username, password) => {
  try {
    console.log('Employee Login request:', { username: username.trim() })
    
    const response = await api.post('/api/auth/employee/login', {
      username: username.trim(), 
      password: password.trim() 
    })
    
    console.log('Employee Login success:', {
      hasToken: !!response.data.token,
      employee_id: response.data.employee_id,
      full_name: response.data.full_name
    })
    
    return response.data
    
  } catch (error) {
    console.error('Employee Login error:', error.response?.data || error.message)
    throw error
  }
}

// Verify token
export const verify = async () => {
  try {
    console.log('Verify request')
    
    const response = await api.get('/api/auth/verify')
    
    console.log('Verify success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Verify error:', error.response?.data || error.message)
    throw error
  }
}

// Logout
export const logoutAdmin = async () => {
  try {
    console.log('🚪 Logout request')
    
    const response = await api.post('/api/auth/logout')
    
    console.log('Logout success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Logout error:', error.response?.data || error.message)
    throw error
  }
}

/**
 * Gửi yêu cầu reset password đến backend
 * @param {string} email
 * @param {string} userType 'admin' | 'employee'
 * @returns {Promise<any>}
 */
export const forgotPassword = async (email, userType) => {
  try {
    console.log(`🔑 Forgot password request for ${userType} with email: ${email}`)
    const response = await api.post('/api/auth/forgot-password', {
      email,
      user_type: userType,
    })
    console.log('Forgot password request successful:', response.data)
    return response.data
  } catch (error) {
    console.error('Forgot password error:', error.response?.data || error.message)
    throw error
  }
}

/**
 * Gửi mật khẩu mới và token để reset password
 * @param {string} token - Token từ URL
 * @param {string} newPassword
 * @param {string} confirmPassword
 * @returns {Promise<any>}
 */
export const resetPassword = async (token, newPassword, confirmPassword) => {
  try {
    console.log('🔐 Reset password request with token...')
    const response = await api.post('/api/auth/reset-password', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    })
    console.log('Password reset successful:', response.data)
    return response.data
  } catch (error) {
    console.error('Password reset error:', error.response?.data || error.message)
    throw error
  }
}