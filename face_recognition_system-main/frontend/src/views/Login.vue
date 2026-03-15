<template>
  <div class="login-wrapper">
    <div class="login-container">
      <div class="bg-decoration-1"></div>
      <div class="bg-decoration-2"></div>
      
      <v-alert
        v-if="connectionError"
        type="error" 
        density="compact"
        class="mb-4"
        closable
        @click:close="connectionError = false"
      >
        {{ connectionError }}
      </v-alert>
      
      <v-card 
        elevation="24" 
        class="login-card"
        rounded="xl"
      >
        <div class="login-header">
          <div class="logo-section">
            <v-icon size="48" color="primary" class="mb-2">mdi-face-recognition</v-icon>
            <h2 class="text-h4 font-weight-bold text-primary mb-1">Employee Management System</h2>
            <p class="text-subtitle-1 text-medium-emphasis">AI-Powered Attendance & HR Portal</p>
          </div>
        </div>

        <v-tabs
          v-model="activeTab"
          align-tabs="center"
          color="primary"
          fixed-tabs
          density="comfortable"
        >
          <v-tab value="admin">
            <v-icon start>mdi-security</v-icon> Admin Login
          </v-tab>
          <v-tab value="employee">
            <v-icon start>mdi-account-group</v-icon> Employee Login
          </v-tab>
        </v-tabs>

        <v-card-text class="login-form-section">
          <v-window v-model="activeTab">
            <v-window-item value="admin">
              <v-form ref="adminLoginForm" @submit.prevent="handleLogin('admin')" :disabled="loading">
                <div class="form-group">
                  <v-text-field
                    v-model="form.adminUsername"
                    label="Username"
                    required
                    prepend-inner-icon="mdi-account-circle"
                    :error-messages="errors.adminUsername"
                    variant="outlined"
                    size="large"
                    class="mb-4"
                    hide-details="auto"
                    :rules="usernameRules"
                    autocomplete="username"
                    @keyup.enter="handleLogin('admin')"
                  ></v-text-field>
                </div>

                <div class="form-group">
                  <v-text-field
                    v-model="form.adminPassword"
                    label="Password"
                    :type="showAdminPassword ? 'text' : 'password'"
                    required
                    prepend-inner-icon="mdi-lock"
                    :append-inner-icon="showAdminPassword ? 'mdi-eye' : 'mdi-eye-off'"
                    @click:append-inner="showAdminPassword = !showAdminPassword"
                    :error-messages="errors.adminPassword"
                    variant="outlined"
                    size="large"
                    class="mb-2"
                    hide-details="auto"
                    :rules="passwordRules"
                    autocomplete="current-password"
                    @keyup.enter="handleLogin('admin')"
                  ></v-text-field>
                </div>
                
                <div class="text-right mb-4">
                  <a
                    href="#"
                    class="text-primary text-decoration-none font-weight-medium"
                    @click.prevent="showForgotPasswordDialog('admin')"
                  >
                    Forgot Password?
                  </a>
                </div>

                <v-btn
                  type="submit"
                  color="primary"
                  block
                  :loading="loading"
                  size="x-large"
                  class="login-btn mb-4"
                  rounded="lg"
                  :disabled="!isFormValid('admin')"
                >
                  <v-icon left class="mr-2">mdi-login</v-icon>
                  {{ loading ? 'Signing In...' : 'Sign In as Admin' }}
                </v-btn>
              </v-form>
            </v-window-item>

            <v-window-item value="employee">
              <v-form ref="employeeLoginForm" @submit.prevent="handleLogin('employee')" :disabled="loading">
                <div class="form-group">
                  <v-text-field
                    v-model="form.employeeUsername"
                    label="Employee ID or Email"
                    required
                    prepend-inner-icon="mdi-badge-account"
                    :error-messages="errors.employeeUsername"
                    variant="outlined"
                    size="large"
                    class="mb-4"
                    hide-details="auto"
                    :rules="usernameRules"
                    autocomplete="username"
                    @keyup.enter="handleLogin('employee')"
                  ></v-text-field>
                </div>

                <div class="form-group">
                  <v-text-field
                    v-model="form.employeePassword"
                    label="Password"
                    :type="showEmployeePassword ? 'text' : 'password'"
                    required
                    prepend-inner-icon="mdi-lock"
                    :append-inner-icon="showEmployeePassword ? 'mdi-eye' : 'mdi-eye-off'"
                    @click:append-inner="showEmployeePassword = !showEmployeePassword"
                    :error-messages="errors.employeePassword"
                    variant="outlined"
                    size="large"
                    class="mb-2"
                    hide-details="auto"
                    :rules="passwordRules"
                    autocomplete="current-password"
                    @keyup.enter="handleLogin('employee')"
                  ></v-text-field>
                </div>
                
                <div class="text-right mb-4">
                  <a
                    href="#"
                    class="text-primary text-decoration-none font-weight-medium"
                    @click.prevent="showForgotPasswordDialog('employee')"
                  >
                    Forgot Password?
                  </a>
                </div>

                <v-btn
                  type="submit"
                  color="secondary"
                  block
                  :loading="loading"
                  size="x-large"
                  class="login-btn mb-4"
                  rounded="lg"
                  :disabled="!isFormValid('employee')"
                >
                  <v-icon left class="mr-2">mdi-account-arrow-right</v-icon>
                  {{ loading ? 'Signing In...' : 'Sign In as Employee' }}
                </v-btn>
              </v-form>
            </v-window-item>
          </v-window>

          <div class="login-options">
            <div class="divider-section">
              <hr class="divider">
              <span class="divider-text">or</span>
              <hr class="divider">
            </div>
            
            <v-btn
              color="success"
              variant="outlined"
              block
              size="large"
              class="facial-recognition-btn"
              rounded="lg"
              @click="goToAttendancePage"
              :disabled="loading"
            >
              <v-icon left class="mr-2">mdi-camera</v-icon>
              Go to Attendance
            </v-btn>
          </div>
        </v-card-text>

        <div class="login-footer">
          <p class="text-caption text-medium-emphasis">
            © 2025 Employee Management System. All rights reserved.
          </p>
        </div>
      </v-card>
      
      <v-dialog v-model="forgotPasswordDialog" max-width="500" persistent>
        <v-card rounded="lg" class="pa-4">
          <v-card-title class="headline text-h5 text-primary font-weight-bold">
            Forgot Password?
          </v-card-title>
          <v-card-text>
            <p class="mb-4">
              Enter the email address associated with your {{ forgotPasswordUserType }} account.
              We'll send you a password reset link.
            </p>

            <v-alert
              v-if="forgotPasswordMessage"
              :type="forgotPasswordMessageType"
              density="compact"
              class="mb-4"
              :closable="!loading"
              @click:close="forgotPasswordMessage = ''"
            >
              {{ forgotPasswordMessage }}
            </v-alert>
            
            <v-form ref="forgotPasswordForm" @submit.prevent="handleForgotPassword">
              <v-text-field
                v-model="forgotPasswordEmail"
                label="Email"
                type="email"
                variant="outlined"
                prepend-inner-icon="mdi-email"
                required
                :rules="emailRules"
                :disabled="hasSentForgotPassword || loading"
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions class="justify-end pa-4">
            <v-btn
              text
              @click="closeForgotPasswordDialog"
              color="grey"
              :disabled="loading"
              v-if="!hasSentForgotPassword"
            >
              Cancel
            </v-btn>
            <v-btn
              color="primary"
              @click="handleForgotPassword"
              :loading="loading"
              :disabled="!isForgotPasswordFormValid || loading"
              v-if="!hasSentForgotPassword"
            >
              Send Reset Link
            </v-btn>
            <v-btn
              color="primary"
              @click="closeForgotPasswordDialog"
              v-if="hasSentForgotPassword"
            >
              OK
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
      
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/Login.css';
import { ref, reactive, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import { login, loginEmployee, verify, forgotPassword } from '../services/api/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

// Tab hiện tại
const activeTab = ref('admin')

// Form data (chia tách cho Admin và Employee)
const form = reactive({
  adminUsername: '',
  adminPassword: '',
  employeeUsername: '',
  employeePassword: '',
})

const errors = reactive({
  adminUsername: '',
  adminPassword: '',
  employeeUsername: '',
  employeePassword: '',
})

// Loading states
const loading = ref(false)
const connectionError = ref('')

// Form validation
const showAdminPassword = ref(false)
const showEmployeePassword = ref(false)
const adminLoginForm = ref(null)
const employeeLoginForm = ref(null)

// Validation rules
const usernameRules = [
  v => !!v || 'Username cannot be empty',
  v => v.length >= 3 || 'Username must have at least 3 characters',
]

const passwordRules = [
  v => !!v || 'Password cannot be empty.',
  v => v.length >= 6 || 'Password must have at least 3 characters',
]

const emailRules = [
  v => !!v || 'Email is required',
  v => /.+@.+\..+/.test(v) || 'E-mail must be valid',
]

// Computed: Kiểm tra tính hợp lệ của form đăng nhập
const isFormValid = computed(() => (type) => {
  if (type === 'admin') {
    return form.adminUsername.trim().length >= 3 && 
           form.adminPassword.trim().length >= 6 &&
           !loading.value
  } else if (type === 'employee') {
    return form.employeeUsername.trim().length >= 3 && 
           form.employeePassword.trim().length >= 6 &&
           !loading.value
  }
  return false
})

// Computed: Kiểm tra tính hợp lệ của form quên mật khẩu
const isForgotPasswordFormValid = computed(() => {
  return /.+@.+\..+/.test(forgotPasswordEmail.value) && forgotPasswordEmail.value.trim() !== ''
})

// Dialog "Quên mật khẩu"
const forgotPasswordDialog = ref(false)
const forgotPasswordEmail = ref('')
const forgotPasswordUserType = ref('')
const forgotPasswordForm = ref(null)

// Trạng thái của dialog quên mật khẩu
const hasSentForgotPassword = ref(false)

// Thông báo trong dialog
const forgotPasswordMessage = ref('')
const forgotPasswordMessageType = ref('info')


// Lifecycle hooks
onMounted(async () => {
  document.body.classList.add('login-page')
  
  if (authStore.isAuthenticated) {
    try {
      console.log('User is authenticated. Verifying session...')
      await verify()
      
      if (authStore.user && authStore.user.role) {
        if (authStore.user.role === 'admin') {
          router.push('/') 
          console.log('Redirecting authenticated Admin to dashboard.')
        } else if (authStore.user.role === 'employee') {
          router.push('/employees')
          console.log('Redirecting authenticated Employee to dashboard.')
        } else {
          router.push('/login')
          console.log('Redirecting authenticated user with unknown role to default home.')
        }
      } else {
        console.warn('Authenticated user has no role defined. Redirecting to default home.')
        router.push('/')
      }
    } catch (error) {
      console.error('Session verification failed:', error)
      authStore.logout()
      connectionError.value = 'Your session has been expired or invalid. Please login again.'
    }
  }
})

onUnmounted(() => {
  document.body.classList.remove('login-page')
})

// Methods
const handleLogin = async (userType) => {
  errors.adminUsername = ''
  errors.adminPassword = ''
  errors.employeeUsername = ''
  errors.employeePassword = ''
  connectionError.value = ''

  let isValid = false
  if (userType === 'admin') {
    if (!isFormValid.value('admin')) {
      return
    }
    const { valid } = await adminLoginForm.value.validate()
    isValid = valid
  } else if (userType === 'employee') {
    if (!isFormValid.value('employee')) {
      return
    }
    const { valid } = await employeeLoginForm.value.validate()
    isValid = valid
  }

  if (!isValid) {
    return
  }

  loading.value = true

  try {
    let loginResponse
    let userData = {}

    if (userType === 'admin') {
      loginResponse = await login(form.adminUsername, form.adminPassword)
      userData = {
        username: loginResponse.username || form.adminUsername,
        admin_id: loginResponse.admin_id,
        role: 'admin',
      }
    } else if (userType === 'employee') {
      loginResponse = await loginEmployee(form.employeeUsername, form.employeePassword)
      userData = {
        employee_id: loginResponse.employee_id,
        full_name: loginResponse.full_name,
        username: loginResponse.employee_id,
        role: 'employee',
        must_change_password: loginResponse.must_change_password,
      }
    }
    
    authStore.login(loginResponse.token, userData)
    
    await nextTick()
    
    try {
      const verifyResponse = await verify()
      if (verifyResponse && verifyResponse.valid) {
        authStore.updateUser({ ...authStore.user, ...verifyResponse })
      }
    } catch (verifyError) {
      if (!authStore.token || !authStore.user) {
        throw new Error('Login failed - no valid token or user data after verification.')
      }
    }
    
    if (authStore.user && authStore.user.role) {
      if (authStore.user.role === 'admin') {
        router.push('/') 
      } else if (authStore.user.role === 'employee') {
        if (authStore.user.must_change_password) {
          router.push('/employee/change-password')
        } else {
          router.push('/employees')
        }
      } else {
        router.push('/')
      }
    } else {
      router.push('/')
    }
    
  } catch (error) {
    const msg = error.response?.data?.error ?? error.message ?? 'Đã xảy ra lỗi trong quá trình đăng nhập.'
    connectionError.value = msg
    
    if (userType === 'admin') {
      errors.adminPassword = msg
    } else if (userType === 'employee') {
      errors.employeePassword = msg
    }
    
    authStore.logout()
    
  } finally {
    loading.value = false
  }
}

const goToAttendancePage = () => {
  router.push('/attendance')
}

// Mở dialog quên mật khẩu
const showForgotPasswordDialog = (userType) => {
  forgotPasswordUserType.value = userType
  forgotPasswordEmail.value = ''
  forgotPasswordMessage.value = ''
  hasSentForgotPassword.value = false
  forgotPasswordDialog.value = true
}

// Đóng dialog quên mật khẩu
const closeForgotPasswordDialog = () => {
  forgotPasswordDialog.value = false
  forgotPasswordEmail.value = ''
  forgotPasswordMessage.value = ''
  hasSentForgotPassword.value = false
}

// Xử lý khi click "Send Reset Link"
const handleForgotPassword = async () => {
  if (!isForgotPasswordFormValid.value) {
    return
  }

  loading.value = true
  forgotPasswordMessage.value = ''
  
  try {
    const response = await forgotPassword(forgotPasswordEmail.value, forgotPasswordUserType.value)
    
    forgotPasswordMessage.value = response.message
    forgotPasswordMessageType.value = 'success'
    hasSentForgotPassword.value = true

  } catch (error) {
    const msg = error.response?.data?.error ?? 'There was an error sending the email. Please try again.'
    forgotPasswordMessage.value = msg
    forgotPasswordMessageType.value = 'error'
    hasSentForgotPassword.value = false

  } finally {
    loading.value = false
  }
}
</script>