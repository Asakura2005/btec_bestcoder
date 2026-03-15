<template>
  <div class="reset-password-wrapper">
    <div class="reset-password-container">
      <v-card 
        elevation="24" 
        class="reset-password-card"
        rounded="xl"
      >
        <div class="card-header">
          <v-icon size="48" color="primary" class="mb-2">mdi-lock-reset</v-icon>
          <h2 class="text-h4 font-weight-bold text-primary mb-1">Reset Password</h2>
          <p class="text-subtitle-1 text-medium-emphasis">Enter your new password below.</p>
        </div>

        <v-card-text>
          <v-alert
            v-if="message"
            :type="messageType" 
            density="compact"
            class="mb-4"
            closable
            @click:close="message = ''"
          >
            {{ message }}
          </v-alert>

          <v-form ref="resetPasswordForm" @submit.prevent="handleResetPassword" :disabled="loading">
            <v-text-field
              v-model="newPassword"
              label="New Password"
              :type="showNewPassword ? 'text' : 'password'"
              required
              prepend-inner-icon="mdi-lock"
              :append-inner-icon="showNewPassword ? 'mdi-eye' : 'mdi-eye-off'"
              @click:append-inner="showNewPassword = !showNewPassword"
              variant="outlined"
              size="large"
              class="mb-4"
              :rules="passwordRules"
            ></v-text-field>

            <v-text-field
              v-model="confirmPassword"
              label="Confirm New Password"
              :type="showConfirmPassword ? 'text' : 'password'"
              required
              prepend-inner-icon="mdi-lock-check"
              :append-inner-icon="showConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
              @click:append-inner="showConfirmPassword = !showConfirmPassword"
              variant="outlined"
              size="large"
              class="mb-4"
              :rules="confirmPasswordRules"
            ></v-text-field>

            <v-btn
              type="submit"
              color="primary"
              block
              :loading="loading"
              size="x-large"
              class="login-btn mb-4"
              rounded="lg"
              :disabled="!isFormValid || loading"
            >
              <v-icon left class="mr-2">mdi-check-circle</v-icon>
              {{ loading ? 'Resetting...' : 'Reset Password' }}
            </v-btn>
          </v-form>
        </v-card-text>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { resetPassword } from '../services/api/auth'

const route = useRoute()
const router = useRouter()

// Form state
const token = ref(route.query.token || '')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

// Alert state
const message = ref('')
const messageType = ref('error')

// Validation rules
const passwordRules = [
  v => !!v || 'New password is required.',
  v => v.length >= 6 || 'Password must be at least 6 characters.',
]

const confirmPasswordRules = [
  v => !!v || 'Confirm password is required.',
  v => v === newPassword.value || 'Passwords do not match.',
]

const isFormValid = computed(() => {
  return newPassword.value.length >= 6 && newPassword.value === confirmPassword.value
})

const handleResetPassword = async () => {
  if (!isFormValid.value || !token.value) {
    message.value = "Invalid token or form data. Please check your information."
    messageType.value = 'error'
    return
  }

  loading.value = true
  message.value = ''

  try {
    const response = await resetPassword(token.value, newPassword.value, confirmPassword.value)
    
    message.value = response.message
    messageType.value = 'success'
    
    // Tự động chuyển hướng về trang login sau 3 giây
    setTimeout(() => {
      router.push('/login')
    }, 3000)

  } catch (error) {
    const msg = error.response?.data?.error || "An error occurred. Please try again."
    message.value = msg
    messageType.value = 'error'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* CSS cho trang Reset Password, bạn có thể thêm vào hoặc import file CSS riêng */
.reset-password-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #f0f2f5;
}

.reset-password-card {
  max-width: 500px;
  width: 100%;
  padding: 24px;
}
</style>