// src/services/api/settings.js
import api from './index'

export const settingsApi = {
  getSettings: async () => {
    try {
      const response = await api.get('/api/settings')
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Get settings error:', error)
      return { success: false, error: error.response?.data?.error || 'Failed to fetch settings' }
    }
  },

  updateSettings: async (data) => {
    try {
      const response = await api.post('/api/settings', data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('Update settings error:', error)
      return { success: false, error: error.response?.data?.error || 'Failed to update settings' }
    }
  },

  createBackup: async () => {
    try {
      const response = await api.post('/api/settings/create-backup')
      return { success: true, message: response.data.message }
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to create backup' }
    }
  },

  resetSystem: async () => {
    try {
      const response = await api.post('/api/settings/reset-system')
      return { success: true, message: response.data.message }
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'Failed to reset system' }
    }
  }
}