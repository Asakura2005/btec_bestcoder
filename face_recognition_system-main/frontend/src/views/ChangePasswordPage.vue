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
            <v-icon size="48" color="primary" class="mb-2">mdi-lock-reset</v-icon>
            <h2 class="text-h4 font-weight-bold text-primary mb-1">Update your password</h2>
            <p class="text-subtitle-1 text-medium-emphasis">For security reasons, please set a new password.</p>
          </div>
        </div>

        <v-card-text class="change-password-form-section">
          <v-form ref="passwordForm" @submit.prevent="handleChangePassword" :disabled="loading">
            <div class="form-group">
              <v-text-field
                v-model="form.oldPassword"
                label="Current password"
                :type="showOldPassword ? 'text' : 'password'"
                required
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showOldPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showOldPassword = !showOldPassword"
                :error-messages="errors.oldPassword"
                variant="outlined"
                size="large"
                class="mb-4"
                hide-details="auto"
                :rules="[v => !!v || 'Current password cannot be empty.']"
              ></v-text-field>
            </div>

            <div class="form-group">
              <v-text-field
                v-model="form.newPassword"
                label="New password"
                :type="showNewPassword ? 'text' : 'password'"
                required
                prepend-inner-icon="mdi-lock-plus"
                :append-inner-icon="showNewPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showNewPassword = !showNewPassword"
                :error-messages="errors.newPassword"
                variant="outlined"
                size="large"
                class="mb-4"
                hide-details="auto"
                :rules="passwordRules"
              ></v-text-field>
            </div>

            <div class="form-group">
              <v-text-field
                v-model="form.confirmPassword"
                label="Confirm password"
                :type="showConfirmPassword ? 'text' : 'password'"
                required
                prepend-inner-icon="mdi-lock-check"
                :append-inner-icon="showConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showConfirmPassword = !showConfirmPassword"
                :error-messages="errors.confirmPassword"
                variant="outlined"
                size="large"
                class="mb-6"
                hide-details="auto"
                :rules="confirmPasswordRules"
              ></v-text-field>
            </div>

            <v-btn
              type="submit"
              color="primary"
              block
              :loading="loading"
              size="x-large"
              class="change-password-btn"
              rounded="lg"
              :disabled="!isFormValid"
            >
              <v-icon left class="mr-2">mdi-check-circle</v-icon>
              {{ loading ? 'Processing...' : 'Change password' }}
            </v-btn>
          </v-form>
        </v-card-text>

        <div class="login-footer">
          <p class="text-caption text-medium-emphasis">
            © 2025 Employee Management System. All rights reserved.
          </p>
        </div>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import '@/assets/css/Login.css'; // Tái sử dụng CSS từ Login
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { employeeChangePassword } from '../services/api';

const router = useRouter();
const authStore = useAuthStore();

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
});

const errors = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
});

const loading = ref(false);
const connectionError = ref('');

const showOldPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);

const passwordForm = ref(null);

// Rules
const passwordRules = [
  v => !!v || 'New password cannot be empty.',
  v => v.length >= 8 || 'Password must be at least 8 characters long.',
  v => /[A-Z]/.test(v) || 'Password must contain at least one uppercase letter.',
  v => /[a-z]/.test(v) || 'Password must contain at least one lowercase letter.',
  v => /[0-9]/.test(v) || 'Password must contain at least one number.',
  v => /[^a-zA-Z0-9]/.test(v) || 'Password must contain at least one special character.',
];

const confirmPasswordRules = [
  v => !!v || 'Password confirmation cannot be empty.',
  v => v === form.newPassword || 'Password confirmation does not match.',
];

// Computed để kiểm tra form valid
const isFormValid = computed(() => {
  // Debug log
  console.log('Form validation:', {
    oldPassword: form.oldPassword.length > 0,
    newPasswordLength: form.newPassword.length >= 8,
    confirmPasswordMatch: form.newPassword === form.confirmPassword && form.confirmPassword.length > 0,
    newPasswordValid: validatePassword(form.newPassword),
    loading: loading.value
  });

  return form.oldPassword.length > 0 && 
         form.newPassword.length >= 8 &&
         form.confirmPassword.length > 0 &&
         form.newPassword === form.confirmPassword &&
         validatePassword(form.newPassword) &&
         !loading.value;
});

// Helper function để validate password
const validatePassword = (password) => {
  if (!password || password.length < 8) return false;
  if (!/[A-Z]/.test(password)) return false;
  if (!/[a-z]/.test(password)) return false;
  if (!/[0-9]/.test(password)) return false;
  if (!/[^a-zA-Z0-9]/.test(password)) return false;
  return true;
};

// Lifecycle hook
onMounted(() => {
  // Đảm bảo chỉ nhân viên cần đổi mật khẩu mới vào được trang này
  if (!authStore.isAuthenticated || authStore.user?.role !== 'employee' || !authStore.user?.must_change_password) {
    router.push('/employees');
  }
});

const handleChangePassword = async () => {
  console.log('Handle change password called');
  
  // Reset errors
  errors.oldPassword = '';
  errors.newPassword = '';
  errors.confirmPassword = '';
  connectionError.value = '';

  // Validate form trước khi submit
  if (!passwordForm.value) {
    console.error('Password form ref is null');
    return;
  }

  const { valid } = await passwordForm.value.validate();
  console.log('Form validation result:', valid);
  
  if (!valid) {
    console.log('Form is not valid, stopping submission');
    return;
  }

  loading.value = true;
  console.log('Loading set to true');

  try {
    console.log('Calling API with:', {
      oldPassword: '***',
      newPassword: '***',
      confirmPassword: '***'
    });

    await employeeChangePassword(form.oldPassword, form.newPassword, form.confirmPassword);

    alert('Your password has been successfully changed! Please log in again with your new password.');

    authStore.logout();
    router.push('/login');

  } catch (error) {
    console.error('Change password error:', error);
    const msg = error.response?.data?.error ?? error.message ?? 'An error occurred while changing the password.';
    connectionError.value = msg;

    if (error.response?.data?.error) {
      if (error.response.data.error.includes('The current password is incorrect.')) {
        errors.oldPassword = error.response.data.error;
      } else if (error.response.data.error.includes('The current password is invalid')) {
        errors.newPassword = error.response.data.error;
      } else if (error.response.data.error.includes('The new password and confirmation password do not match.')) {
        errors.confirmPassword = error.response.data.error;
      }
    }
  } finally {
    loading.value = false;
    console.log('Loading set to false');
  }
};
</script>

<style scoped>
/* Override login form section for change password */
.change-password-form-section {
  padding: 25px 30px !important;
}

/* Change password button specific styles */
.change-password-btn {
  font-weight: 500 !important;
  text-transform: none !important;
  letter-spacing: 0.3px !important;
  transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out !important;
  pointer-events: auto !important; /* Ensure button is clickable */
  position: relative !important;
  z-index: 10 !important;
}

.change-password-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 15px rgba(var(--v-theme-primary), 0.2);
}

/* Override any potential disabled styles */
.change-password-btn:not(:disabled) {
  opacity: 1 !important;
  cursor: pointer !important;
}

/* Ensure form elements are not overlapping */
.form-group {
  position: relative;
  z-index: 1;
}

/* Debug styles - remove after fixing */
.change-password-btn {
  border: 2px solid red !important; /* Temporary for debugging */
}

.change-password-btn:disabled {
  border: 2px solid gray !important; /* Temporary for debugging */
  opacity: 0.5 !important;
}
</style>