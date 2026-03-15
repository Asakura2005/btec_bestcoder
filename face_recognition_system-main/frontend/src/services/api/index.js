// src/services/api/index.js
import axios from 'axios'
import { useAuthStore } from '../../stores/auth'
import router from '../../router'

// Tạo axios instance
const api = axios.create({
  baseURL: '',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()

    // Đảm bảo store đã được khởi tạo
    if (!authStore.isInitialized) {
      authStore.initializeFromStorage()
    }

    const token = authStore.token

    console.log("Request interceptor:", {
      url: config.url,
      hasToken: !!token,
      isAuthenticated: authStore.isAuthenticated
    })

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
      console.log("Authorization header set")
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log("API Success:", response.config.url, response.status)
    return response
  },
  (error) => {
    const authStore = useAuthStore()

    console.log("API Error:", {
      url: error.config?.url,
      status: error.response?.status,
      data: error.response?.data
    })

    if (error.response?.status === 401) {
      console.log("401 Unauthorized - Token expired or invalid")

      // Chỉ logout nếu không phải request login
      if (!error.config?.url?.includes('/api/auth/admin/login') && !error.config?.url?.includes('/api/auth/employee/login')) {
        authStore.logout()

        // Redirect về login với current route
        const currentRoute = router.currentRoute.value
        if (currentRoute.name !== 'Login') {
          router.push({
            name: 'Login',
            query: { redirect: currentRoute.fullPath }
          })
        }
      }
    }

    // Xử lý lỗi network
    if (error.code === 'ECONNABORTED') {
      error.message = 'Connection timeout. Please try again.'
    } else if (error.code === 'ERR_NETWORK') {
      error.message = 'Cannot connect to the server. Please check your network connection.'
    }

    return Promise.reject(error)
  }
)

export default api