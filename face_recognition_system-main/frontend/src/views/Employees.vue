<template>
  <div class="employee-dashboard">
    <!-- Background Elements -->
    <div class="bg-gradient"></div>
    <div class="bg-pattern"></div>
    
    <!-- Header -->
    <header class="employee-header">
      <div class="header-content">
        <div class="brand-section">
          <div class="brand-icon">
            <v-icon size="40" color="white">mdi-account-circle</v-icon>
          </div>
          <div class="brand-text">
            <h1 class="brand-title">Welcome, {{ authStore.user?.full_name || authStore.user?.employee_id || 'Employee' }}!</h1>
            <p class="brand-subtitle">Your Employee ID: {{ authStore.user?.employee_id || 'N/A' }}</p>
          </div>
        </div>
        
        <div class="header-actions">
          <v-btn
            class="header-btn"
            variant="outlined"
            color="white"
            prepend-icon="mdi-key"
            @click="showChangePasswordDialog = true"
          >
            Change Password
          </v-btn>
          <v-btn
            class="header-btn logout-btn"
            variant="outlined"
            color="white"
            prepend-icon="mdi-logout"
            @click="handleLogout"
          >
            Logout
          </v-btn>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <div class="content-container">
        <!-- Navigation Tabs -->
        <div class="nav-tabs">
          <button 
            v-for="tab in tabs" 
            :key="tab.value"
            :class="['nav-tab', { active: currentTab === tab.value }]"
            @click="currentTab = tab.value"
          >
            <v-icon :icon="tab.icon" size="20" class="tab-icon"></v-icon>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
          <transition name="fade" mode="out-in">
            <!-- Attendance Summary -->
            <div v-if="currentTab === 'summary'" class="content-panel">
              <div class="panel-content">
                <div v-if="attendanceReport" class="summary-section">
                  <div class="summary-header">
                    <h2 class="section-title">
                      <v-icon>mdi-chart-line</v-icon>
                      Attendance Summary
                    </h2>
                    <v-chip color="blue" variant="outlined" size="small">
                      {{ attendanceReport.period?.start_date }} - {{ attendanceReport.period?.end_date }}
                    </v-chip>
                  </div>

                  <div class="stats-grid">
                    <div class="stat-card normal">
                      <div class="stat-value">{{ attendanceReport.report?.normal_days || 0 }}</div>
                      <div class="stat-label">Normal Days</div>
                    </div>
                    <div class="stat-card late">
                      <div class="stat-value">{{ attendanceReport.report?.late_days || 0 }}</div>
                      <div class="stat-label">Late Days</div>
                    </div>
                    <div class="stat-card half">
                      <div class="stat-value">{{ attendanceReport.report?.half_days || 0 }}</div>
                      <div class="stat-label">Half Days</div>
                    </div>
                    <div class="stat-card recovered">
                      <div class="stat-value">{{ attendanceReport.report?.recovered_days || 0 }}</div>
                      <div class="stat-label">Recovered Days</div>
                    </div>
                    <div class="stat-card absent">
                      <div class="stat-value">{{ attendanceReport.report?.absent_days || 0 }}</div>
                      <div class="stat-label">Absent Days</div>
                    </div>
                  </div>

                  <div class="metrics-grid">
                    <div class="metric-card blue">
                      <div class="metric-content">
                        <div class="metric-info">
                          <div class="metric-value">{{ attendanceReport.report?.attendance_rate }}%</div>
                          <div class="metric-label">Attendance Rate</div>
                        </div>
                        <v-icon size="30" color="white">mdi-calendar-check</v-icon>
                      </div>
                    </div>
                    <div class="metric-card green">
                      <div class="metric-content">
                        <div class="metric-info">
                          <div class="metric-value">{{ attendanceReport.report?.total_work_hours }}h</div>
                          <div class="metric-label">Total Work Hours</div>
                        </div>
                        <v-icon size="30" color="white">mdi-clock</v-icon>
                      </div>
                    </div>
                  </div>

                  <div class="additional-stats">
                    <div class="stat-item">
                      <div class="stat-value">{{ attendanceReport.report?.avg_checkin_time || 'N/A' }}</div>
                      <div class="stat-label">Avg Check-in</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ attendanceReport.report?.avg_checkout_time || 'N/A' }}</div>
                      <div class="stat-label">Avg Check-out</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ attendanceReport.report?.total_overtime_hours }}h</div>
                      <div class="stat-label">Overtime Hours</div>
                    </div>
                    <div class="stat-item">
                      <div class="stat-value">{{ attendanceReport.report?.forgot_checkout_days }}</div>
                      <div class="stat-label">Forgot Checkout</div>
                    </div>
                  </div>
                </div>
                <div v-else class="loading-section">
                  <v-progress-circular indeterminate color="primary" size="50"></v-progress-circular>
                  <p class="loading-text">Loading attendance summary...</p>
                </div>
              </div>
            </div>

            <!-- Daily Attendance -->
            <div v-else-if="currentTab === 'daily'" class="content-panel">
              <div class="panel-content">
                <div class="section-header">
                  <h2 class="section-title">
                    <v-icon>mdi-calendar-clock</v-icon>
                    Daily Attendance Details
                  </h2>
                </div>

                <div class="filter-section">
                  <div class="filter-row">
                    <v-text-field
                      v-model="historyFilters.startDate"
                      label="Start Date"
                      type="date"
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      class="filter-field"
                    ></v-text-field>
                    <v-text-field
                      v-model="historyFilters.endDate"
                      label="End Date"
                      type="date"
                      variant="outlined"
                      density="comfortable"
                      hide-details
                      class="filter-field"
                    ></v-text-field>
                    <v-btn
                      color="primary"
                      size="large"
                      @click="fetchAttendanceHistory"
                      :loading="historyLoading"
                      class="filter-btn"
                    >
                      <v-icon left>mdi-filter</v-icon> Filter
                    </v-btn>
                  </div>
                </div>

                <!-- Cập nhật phần table trong Daily Details tab -->
                <div class="table-container">
                  <v-data-table
                    :headers="dailyAttendanceHeaders"
                    :items="dailyAttendanceRecords"
                    :loading="historyLoading"
                    class="attendance-table"
                    :items-per-page="15"
                    item-value="date"
                  >
                    <template v-slot:no-data>
                      <div class="no-data">
                        <v-icon size="50" color="grey">mdi-calendar-remove</v-icon>
                        <p>No attendance records found for the selected period.</p>
                      </div>
                    </template>
                    
                    <template v-slot:item.date="{ item }">
                      <div class="date-cell">
                        <strong>{{ formatSimpleDate(item.date) }}</strong>
                      </div>
                    </template>
                    
                    <template v-slot:item.status="{ item }">
                      <v-chip :color="getStatusColor(item.status)" label small>
                        {{ formatStatus(item.status) }}
                      </v-chip>
                    </template>
                    
                    <template v-slot:item.attendance_type="{ item }">
                      <v-chip 
                        v-if="item.attendance_type && item.attendance_type !== 'absent'" 
                        :color="getAttendanceTypeColor(item.attendance_type)" 
                        label 
                        small
                      >
                        {{ formatAttendanceType(item.attendance_type) }}
                      </v-chip>
                      <span v-else class="text-disabled">-</span>
                    </template>
                    
                    <template v-slot:item.checkin_time="{ item }">
                      <span v-if="item.checkin_time && item.attendance_type !== 'recovered'" class="time-cell">{{ item.checkin_time }}</span>
                      <span v-else-if="item.attendance_type === 'recovered'" class="text-teal">
                        <small><em>{{ getRecoveredTime('checkin') }}*</em></small>
                      </span>
                      <span v-else class="text-disabled">-</span>
                    </template>
                      
                    <template v-slot:item.checkout_time="{ item }">
                      <span v-if="item.checkout_time && item.attendance_type !== 'recovered'" class="time-cell">{{ item.checkout_time }}</span>
                      <span v-else-if="item.attendance_type === 'recovered'" class="text-teal">
                        <small><em>{{ getRecoveredTime('checkout') }}*</em></small>
                      </span>
                      <span v-else class="text-disabled">-</span>
                    </template>
                    
                    <template v-slot:item.work_hours="{ item }">
                      <span v-if="item.work_hours > 0" class="hours-cell">
                        {{ item.work_hours }}h
                        <span v-if="item.attendance_type === 'recovered'" class="text-teal">*</span>
                      </span>
                      <span v-else class="text-disabled">-</span>
                    </template>
                    
                    <template v-slot:item.late_minutes="{ item }">
                      <v-chip 
                        v-if="item.late_minutes > 0" 
                        color="orange" 
                        size="x-small"
                        variant="text"
                      >
                        +{{ item.late_minutes }}min
                      </v-chip>
                      <span v-else class="text-disabled">-</span>
                    </template>
                    
                    <template v-slot:item.early_minutes="{ item }">
                      <v-chip 
                        v-if="item.early_minutes > 0" 
                        color="red" 
                        size="x-small"
                        variant="text"
                      >
                        -{{ item.early_minutes }}min
                      </v-chip>
                      <span v-else class="text-disabled">-</span>
                    </template>
                    
                    <template v-slot:item.overtime_hours="{ item }">
                      <v-chip 
                        v-if="item.overtime_hours > 0" 
                        color="green" 
                        size="x-small"
                        variant="text"
                      >
                        +{{ item.overtime_hours }}h
                      </v-chip>
                      <span v-else class="text-disabled">-</span>
                    </template>

                    <template v-slot:item.notes="{ item }">
                      <span 
                        v-if="item.notes && item.notes !== 'Normal'" 
                        class="notes-cell"
                        :class="{ 'text-teal': item.attendance_type === 'recovered' }"
                      >
                        {{ item.notes }}
                      </span>
                      <span v-else class="text-disabled">Normal</span>
                    </template>
                  </v-data-table>
                </div>

                <!-- Thêm legend giải thích -->
                <div class="table-legend">
                  <v-alert type="info" variant="tonal" density="compact" class="mt-4">
                    <strong>Legend:</strong>
                    <ul class="legend-list">
                      <li><strong>*</strong> = Standard times for recovered attendance</li>
                      <li><v-chip color="teal" size="x-small" label>Recovered</v-chip> = Attendance restored by admin approval</li>
                      <li><v-chip color="red" size="x-small" label>Incomplete</v-chip> = Missing check-in or check-out</li>
                      <li><v-chip color="purple" size="x-small" label>Half Day</v-chip> = Arrived during lunch hours</li>
                    </ul>
                  </v-alert>
                </div>
              </div>
            </div>

            <!-- Recovery Request -->
            <div v-else-if="currentTab === 'recovery'" class="content-panel">
              <div class="panel-content">
                <div class="section-header">
                  <h2 class="section-title">
                    <v-icon>mdi-restore</v-icon>
                    Request Attendance Recovery
                  </h2>
                </div>

                <div class="form-container">
                  <v-form @submit.prevent="submitRecoveryRequest" ref="recoveryFormRef" class="recovery-form">
                    <v-text-field
                      v-model="recoveryForm.request_date"
                      label="Date of Missed Attendance"
                      type="date"
                      variant="outlined"
                      density="comfortable"
                      class="form-field"
                      :rules="[rules.required]"
                    ></v-text-field>

                    <v-textarea
                      v-model="recoveryForm.reason"
                      label="Reason (e.g., Forgot to check-in, System error, etc.)"
                      variant="outlined"
                      density="comfortable"
                      rows="4"
                      class="form-field"
                      :rules="[rules.required, rules.minLength(10)]"
                    ></v-textarea>

                    <v-alert
                      v-if="recoveryErrorMessage"
                      type="error"
                      closable
                      class="form-alert"
                      variant="tonal"
                      density="compact"
                      @click:close="recoveryErrorMessage = ''"
                    >
                      {{ recoveryErrorMessage }}
                    </v-alert>

                    <v-alert
                      v-if="recoverySuccessMessage"
                      type="success"
                      closable
                      class="form-alert"
                      variant="tonal"
                      density="compact"
                      @click:close="recoverySuccessMessage = ''"
                    >
                      {{ recoverySuccessMessage }}
                    </v-alert>

                    <v-btn
                      type="submit"
                      color="primary"
                      block
                      size="large"
                      :loading="recoveryLoading"
                      class="submit-btn"
                    >
                      <v-icon left>mdi-send</v-icon> Submit Request
                    </v-btn>
                  </v-form>
                </div>
              </div>
            </div>

            <!-- My Requests -->
            <div v-else-if="currentTab === 'requests'" class="content-panel">
              <div class="panel-content">
                <div class="section-header">
                  <h2 class="section-title">
                    <v-icon>mdi-history</v-icon>
                    My Recovery Requests
                  </h2>
                  <v-btn
                    color="primary"
                    variant="text"
                    size="small"
                    @click="fetchMyRecoveryRequests"
                    :loading="myRecoveryRequestsLoading"
                    class="refresh-btn"
                  >
                    <v-icon left>mdi-refresh</v-icon>
                    Refresh
                  </v-btn>
                </div>

                <div class="table-container">
                  <v-data-table
                    :headers="recoveryRequestHeaders"
                    :items="myRecoveryRequests"
                    :loading="myRecoveryRequestsLoading"
                    class="requests-table"
                    :items-per-page="10"
                  >
                    <template v-slot:no-data>
                      <div class="no-data">
                        <v-icon size="50" color="grey">mdi-file-document-outline</v-icon>
                        <p>No recovery requests found.</p>
                      </div>
                    </template>
                    <template v-slot:item.request_date="{ item }">
                      {{ formatDate(item.request_date) }}
                    </template>
                    <template v-slot:item.status="{ item }">
                      <v-chip :color="getRecoveryStatusColor(item.status)" label small>
                        {{ item.status }}
                      </v-chip>
                    </template>
                    <template v-slot:item.created_at="{ item }">
                      {{ formatDateTime(item.created_at) }}
                    </template>
                    <template v-slot:item.notes="{ item }">
                      <span v-if="item.notes" class="notes-cell">{{ item.notes }}</span>
                      <span v-else class="text-disabled">No notes</span>
                    </template>
                  </v-data-table>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </main>

    <!-- Change Password Dialog -->
    <v-dialog v-model="showChangePasswordDialog" max-width="500px" persistent>
      <v-card class="dialog-card">
        <v-card-title class="dialog-header">
          <v-icon left>mdi-key</v-icon>
          Change Password
        </v-card-title>
        <v-card-text class="dialog-content">
          <v-form @submit.prevent="changePassword" ref="passwordFormRef">
            <v-text-field
              v-model="passwordForm.oldPassword"
              label="Current Password"
              type="password"
              variant="outlined"
              density="comfortable"
              class="dialog-field"
              :rules="[rules.required]"
              :error-messages="passwordErrorMessage"
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.newPassword"
              label="New Password"
              type="password"
              variant="outlined"
              density="comfortable"
              class="dialog-field"
              :rules="[rules.required, rules.minLength(6)]"
            ></v-text-field>

            <v-text-field
              v-model="passwordForm.confirmNewPassword"
              label="Confirm New Password"
              type="password"
              variant="outlined"
              density="comfortable"
              class="dialog-field"
              :rules="[rules.required, rules.passwordMatch]"
            ></v-text-field>

            <v-alert
              v-if="passwordSuccessMessage"
              type="success"
              class="dialog-alert"
              variant="tonal"
              density="compact"
            >
              {{ passwordSuccessMessage }}
            </v-alert>
          </v-form>
        </v-card-text>
        <v-card-actions class="dialog-actions">
          <v-spacer></v-spacer>
          <v-btn
            color="grey"
            variant="text"
            @click="closePasswordDialog"
            :disabled="passwordLoading"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="changePassword"
            :loading="passwordLoading"
          >
            Change Password
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Global Snackbar for notifications -->
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
      location="top"
    >
      {{ snackbarMessage }}
      <template v-slot:actions>
        <v-btn
          color="white"
          variant="text"
          @click="showSnackbar = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue';
import { useAuthStore } from '../stores/auth';
import * as api from '@/services/api'; 
import { useRouter } from 'vue-router';
import '@/assets/css/Employees.css';

const authStore = useAuthStore();
const router = useRouter();
const companySettings = ref(null);

// Current tab state
const currentTab = ref('summary');

// Tab definitions
const tabs = [
  {
    value: 'summary',
    label: 'Attendance Summary',
    icon: 'mdi-chart-line'
  },
  {
    value: 'daily',
    label: 'Daily Details',
    icon: 'mdi-calendar-clock'
  },
  {
    value: 'recovery',
    label: 'Request Recovery',
    icon: 'mdi-restore'
  },
  {
    value: 'requests',
    label: 'My Requests',
    icon: 'mdi-history'
  }
];

// --- Enhanced Attendance History State ---
const attendanceReport = ref(null);
const dailyAttendanceRecords = ref([]);
const historyLoading = ref(false);
const historyFilters = reactive({
  startDate: '',
  endDate: '',
});

// Updated headers for daily attendance details
const dailyAttendanceHeaders = [
  { title: 'Date', key: 'date', sortable: true, width: '120px' },
  { title: 'Check-in', key: 'checkin_time', sortable: false, width: '100px' },
  { title: 'Check-out', key: 'checkout_time', sortable: false, width: '100px' },
  { title: 'Work Hours', key: 'work_hours', sortable: true, width: '100px' },
  { title: 'Overtime', key: 'overtime_hours', sortable: true, width: '90px' },
  { title: 'Status', key: 'status', sortable: true, width: '100px' },
  // { title: 'Type', key: 'attendance_type', sortable: true, width: '110px' },
  { title: 'Notes', key: 'notes', sortable: false, width: '150px' },
];

// --- Attendance Recovery Request State ---
const recoveryForm = reactive({
  request_date: '',
  reason: '',
});
const recoveryLoading = ref(false);
const recoveryErrorMessage = ref('');
const recoverySuccessMessage = ref('');
const recoveryFormRef = ref(null);

// --- My Recovery Requests State ---
const myRecoveryRequests = ref([]);
const myRecoveryRequestsLoading = ref(false);

const recoveryRequestHeaders = [
  { title: 'Request ID', key: 'request_id', sortable: false },
  { title: 'Date', key: 'request_date', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Submitted', key: 'created_at', sortable: true },
  { title: 'Admin Notes', key: 'notes', sortable: false },
];

// --- Change Password State ---
const showChangePasswordDialog = ref(false);
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmNewPassword: '',
});
const passwordLoading = ref(false);
const passwordErrorMessage = ref('');
const passwordSuccessMessage = ref('');
const passwordFormRef = ref(null);

// --- Global Snackbar State ---
const showSnackbar = ref(false);
const snackbarMessage = ref('');
const snackbarColor = ref('success');

// --- Validation Rules ---
const rules = {
  required: value => !!value || 'This field is required.',
  minLength: (length) => value => (value && value.length >= length) || `Must be at least ${length} characters.`,
  passwordMatch: value => value === passwordForm.newPassword || 'Passwords do not match.',
};

// --- Computed Properties ---
const getAttendanceTypeColor = (type) => {
  switch (type) {
    case 'normal': return 'blue';
    case 'late': return 'orange';
    case 'half_day': return 'purple';
    case 'incomplete': return 'red';
    case 'recovered': return 'teal';
    default: return 'grey';
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case 'present': return 'green';
    case 'absent': return 'red';
    case 'present_incomplete': return 'orange';
    default: return 'grey';
  }
};

const getRecoveryStatusColor = (status) => {
  switch (status) {
    case 'pending': return 'orange';
    case 'approved': return 'green';
    case 'rejected': return 'red';
    default: return 'grey';
  }
};

// --- Utility Methods ---

const formatStatus = (status) => {
  switch (status) {
    case 'present': return 'Present';
    case 'absent': return 'Absent';
    case 'present_incomplete': return 'Present (Incomplete)';
    default: return status;
  }
};

const formatAttendanceType = (type) => {
  switch (type) {
    case 'normal': return 'Normal';
    case 'late': return 'Late';
    case 'half_day': return 'Half Day';
    case 'recovered': return 'Recovered';
    case 'incomplete': return 'Incomplete';
    default: return type;
  }
};

// New simplified date format function
const formatSimpleDate = (dateString) => {
  if (!dateString) return '';
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', { 
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
};

const showNotification = (message, color = 'success') => {
  snackbarMessage.value = message;
  snackbarColor.value = color;
  showSnackbar.value = true;
};

const formatDateTime = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleString('en-GB', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  });
};

const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString('en-GB');
};

// --- Main Methods ---
const fetchAttendanceHistory = async () => {
  historyLoading.value = true;
  try {
    const params = {};
    if (historyFilters.startDate) {
      params.start_date = historyFilters.startDate;
    }
    if (historyFilters.endDate) {
      params.end_date = historyFilters.endDate;
    }
    
    const response = await api.getMyAttendanceHistory(params);
    console.log('Attendance response:', response);
    
    // Store the full report
    attendanceReport.value = response;
    
    // THÊM DÒNG NÀY - lưu company settings từ backend
    if (response.report?.company_settings) {
      companySettings.value = response.report.company_settings;
    }
    
    // Extract daily records và thêm notes cho từng ngày
    const dailyRecords = response.report?.daily_records || [];
    
    // Thêm logic tạo notes cho mỗi ngày
    dailyAttendanceRecords.value = dailyRecords.map(record => ({
      ...record,
      notes: generateDayNotes(record)
    }));
    
    showNotification(`Loaded attendance report for ${dailyAttendanceRecords.value.length} days`);
  } catch (error) {
    console.error('Error fetching attendance history:', error);
    showNotification('Failed to fetch attendance history', 'error');
    attendanceReport.value = null;
    dailyAttendanceRecords.value = [];
  } finally {
    historyLoading.value = false;
  }
};

const getRecoveredTime = (type) => {
  if (!companySettings.value) {
    return type === 'checkin' ? '08:00:00' : '17:00:00'; // fallback
  }
  return type === 'checkin' ? companySettings.value.start_work : companySettings.value.end_work;
};

const generateDayNotes = (record) => {
  const notes = [];
  
  // Kiểm tra status
  if (record.status === 'absent') {
    return ' ';
  }
  
  // Kiểm tra attendance_type
  if (record.attendance_type === 'recovered') {
    notes.push('Recovered');
  } else if (record.attendance_type === 'incomplete') {
    notes.push('Incomplete');
  } else if (record.attendance_type === 'half_day') {
    notes.push('Half Day');
  }
  
  // Kiểm tra late
  if (record.late_minutes > 15) { // Assuming 15 min threshold
    notes.push('Late Arrival');
  }
  
  // Kiểm tra early departure
  if (record.early_minutes > 15) {
    notes.push('Early Leave');
  }
  
  // Kiểm tra forgot checkout
  if (record.checkin_time && !record.checkout_time && record.attendance_type !== 'recovered') {
    notes.push('Forgot Checkout');
  }
  
  // Kiểm tra overtime
  if (record.overtime_hours > 0) {
    notes.push('Overtime');
  }
  
  return notes.length > 0 ? notes.join(', ') : 'Normal';
};

const fetchMyRecoveryRequests = async () => {
  myRecoveryRequestsLoading.value = true;
  try {
    const requests = await api.getEmployeeRecoveryRequests();
    myRecoveryRequests.value = requests || [];
  } catch (error) {
    console.error('Error fetching my recovery requests:', error);
    showNotification('Failed to fetch recovery requests', 'error');
  } finally {
    myRecoveryRequestsLoading.value = false;
  }
};

const submitRecoveryRequest = async () => {
  const { valid } = await recoveryFormRef.value.validate();
  if (!valid) return;

  recoveryLoading.value = true;
  recoveryErrorMessage.value = '';
  recoverySuccessMessage.value = '';

  try {
    const payload = {
      request_date: recoveryForm.request_date,
      reason: recoveryForm.reason.trim(),
    };

    const response = await api.submitEmployeeRecoveryRequest(payload);
    
    recoverySuccessMessage.value = response.message || 'Recovery request submitted successfully!';
    
    // Clear form
    recoveryForm.request_date = '';
    recoveryForm.reason = '';
    recoveryFormRef.value.resetValidation();
    
    // Refresh recovery requests list
    fetchMyRecoveryRequests();
    
    showNotification('Recovery request submitted successfully!');

  } catch (error) {
    recoveryErrorMessage.value = error.response?.data?.error || 'Failed to submit request. Please try again.';
    console.error('Error submitting recovery request:', error);
  } finally {
    recoveryLoading.value = false;
  }
};

const changePassword = async () => {
  const { valid } = await passwordFormRef.value.validate();
  if (!valid) return;

  passwordLoading.value = true;
  passwordErrorMessage.value = '';
  passwordSuccessMessage.value = '';

  try {
    const response = await api.employeeChangePassword(
      passwordForm.oldPassword,
      passwordForm.newPassword,
      passwordForm.confirmNewPassword
    );

    passwordSuccessMessage.value = response.message || 'Password changed successfully!';
    
    // Clear form after success
    setTimeout(() => {
      closePasswordDialog();
      showNotification('Password changed successfully!');
    }, 1500);

  } catch (error) {
    passwordErrorMessage.value = error.response?.data?.error || 'Failed to change password. Please check your current password.';
    console.error('Error changing password:', error);
  } finally {
    passwordLoading.value = false;
  }
};

const closePasswordDialog = () => {
  showChangePasswordDialog.value = false;
  passwordForm.oldPassword = '';
  passwordForm.newPassword = '';
  passwordForm.confirmNewPassword = '';
  passwordErrorMessage.value = '';
  passwordSuccessMessage.value = '';
  if (passwordFormRef.value) {
    passwordFormRef.value.resetValidation();
  }
};

const handleLogout = async () => {
  try {
    await authStore.logout();
    router.push('/login');
    showNotification('Logged out successfully');
  } catch (error) {
    console.error('Logout error:', error);
    // Force redirect even if logout API fails
    router.push('/login');
  }
};

// --- Lifecycle Hooks ---
onMounted(() => {
  // Set default date range to current month if not set
  if (!historyFilters.startDate || !historyFilters.endDate) {
    const now = new Date();
    const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
    const lastDay = new Date(now.getFullYear(), now.getMonth() + 1, 0);
    
    historyFilters.startDate = firstDay.toISOString().split('T')[0];
    historyFilters.endDate = lastDay.toISOString().split('T')[0];
  }

  fetchAttendanceHistory();
  fetchMyRecoveryRequests();
});
</script>