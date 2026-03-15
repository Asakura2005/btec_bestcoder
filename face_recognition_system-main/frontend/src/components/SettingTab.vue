<!-- src/components/SettingsTab.vue -->
<template>
  <div class="settings-container">
    <!-- Header -->
    <div class="settings-header">
      <div class="header-content">
        <div class="header-info">
          <h2 class="settings-title">System Settings</h2>
          <p class="settings-subtitle">Configure attendance system parameters and policies</p>
        </div>
        <div class="header-actions">
          <v-btn
            variant="outlined"
            color="orange-darken-2"
            prepend-icon="mdi-restore"
            @click="resetAllSettings"
            :disabled="!hasUnsavedChanges"
          >
            Reset All
          </v-btn>
          <v-btn
            color="primary"
            prepend-icon="mdi-content-save"
            @click="saveAllSettings"
            :disabled="!hasUnsavedChanges"
            :loading="saving"
          >
            Save Changes
          </v-btn>
        </div>
      </div>
    </div>

    <!-- Settings Content -->
    <div class="settings-content">
      <!-- 1. Time Management -->
      <div class="settings-card time-management">
        <div class="card-header">
          <div class="header-icon">
            <v-icon color="primary" size="24">mdi-clock-outline</v-icon>
          </div>
          <div>
            <h3 class="card-title">Time Management</h3>
            <p class="card-subtitle">Configure working hours and attendance time windows</p>
          </div>
          <v-switch
            v-model="timeSettings.enabled"
            color="primary"
            hide-details
            @change="markAsChanged"
          ></v-switch>
        </div>
        
        <div class="card-content" v-if="timeSettings.enabled">
          <div class="settings-grid">
            <!-- Working Hours -->
            <div class="setting-group">
              <label class="setting-label">Standard Work Start Time</label>
              <v-text-field
                v-model="timeSettings.workStartTime"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Standard Work End Time</label>
              <v-text-field
                v-model="timeSettings.workEndTime"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <!-- Check-in Window -->
            <div class="setting-group">
              <label class="setting-label">Earliest Check-in Time</label>
              <v-text-field
                v-model="timeSettings.checkinStart"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Latest Check-in Time</label>
              <v-text-field
                v-model="timeSettings.checkinEnd"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <!-- Lunch Break -->
            <div class="setting-group">
              <label class="setting-label">Lunch Break Start</label>
              <v-text-field
                v-model="timeSettings.lunchStart"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Lunch Break End</label>
              <v-text-field
                v-model="timeSettings.lunchEnd"
                type="time"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <!-- Minimum Work Hours -->
            <div class="setting-group full-width">
              <label class="setting-label">Minimum Work Hours Before Check-out</label>
              <div class="slider-container">
                <v-slider
                  v-model="timeSettings.minWorkHours"
                  min="1"
                  max="12"
                  step="0.5"
                  thumb-label
                  color="primary"
                  @input="markAsChanged"
                >
                  <template v-slot:append>
                    <div class="slider-value">{{ timeSettings.minWorkHours }}h</div>
                  </template>
                </v-slider>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. System Policies -->
      <div class="settings-card policies">
        <div class="card-header">
          <div class="header-icon">
            <v-icon color="success" size="24">mdi-shield-check-outline</v-icon>
          </div>
          <div>
            <h3 class="card-title">System Policies</h3>
            <p class="card-subtitle">Define attendance rules and regulations</p>
          </div>
          <v-switch
            v-model="policySettings.enabled"
            color="success"
            hide-details
            @change="markAsChanged"
          ></v-switch>
        </div>
        
        <div class="card-content" v-if="policySettings.enabled">
          <div class="settings-grid">
            <div class="setting-group">
              <label class="setting-label">Max Check-ins Per Day</label>
              <v-text-field
                v-model.number="policySettings.maxCheckins"
                type="number"
                min="1"
                max="10"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Max Check-outs Per Day</label>
              <v-text-field
                v-model.number="policySettings.maxCheckouts"
                type="number"
                min="1"
                max="10"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Late Arrival Grace Period (minutes)</label>
              <div class="slider-container">
                <v-slider
                  v-model="policySettings.gracePeriod"
                  min="0"
                  max="30"
                  step="5"
                  thumb-label
                  color="success"
                  @input="markAsChanged"
                >
                  <template v-slot:append>
                    <div class="slider-value">{{ policySettings.gracePeriod }}min</div>
                  </template>
                </v-slider>
              </div>
            </div>

            <div class="setting-group">
              <label class="setting-label">Overtime Threshold (hours)</label>
              <div class="slider-container">
                <v-slider
                  v-model="policySettings.overtimeThreshold"
                  min="6"
                  max="12"
                  step="0.5"
                  thumb-label
                  color="success"
                  @input="markAsChanged"
                >
                  <template v-slot:append>
                    <div class="slider-value">{{ policySettings.overtimeThreshold }}h</div>
                  </template>
                </v-slider>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 3. Notifications & Alerts -->
      <div class="settings-card notifications">
        <div class="card-header">
          <div class="header-icon">
            <v-icon color="warning" size="24">mdi-bell-outline</v-icon>
          </div>
          <div>
            <h3 class="card-title">Notifications & Alerts</h3>
            <p class="card-subtitle">Configure system notifications and reminders</p>
          </div>
          <v-switch
            v-model="notificationSettings.enabled"
            color="warning"
            hide-details
            @change="markAsChanged"
          ></v-switch>
        </div>
        
        <div class="card-content" v-if="notificationSettings.enabled">
          <div class="notification-options">
            <div class="notification-item">
              <div class="notification-info">
                <h4>Admin Alerts</h4>
                <p>Receive notifications for attendance anomalies</p>
              </div>
              <v-switch
                v-model="notificationSettings.adminAlerts"
                color="warning"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>

            <div class="notification-item">
              <div class="notification-info">
                <h4>Employee Reminders</h4>
                <p>Send check-out reminders to employees</p>
              </div>
              <v-switch
                v-model="notificationSettings.employeeReminders"
                color="warning"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>

            <div class="notification-item">
              <div class="notification-info">
                <h4>System Health Monitoring</h4>
                <p>Alert when system errors occur</p>
              </div>
              <v-switch
                v-model="notificationSettings.systemHealth"
                color="warning"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>

            <div class="notification-item">
              <div class="notification-info">
                <h4>Daily Reports</h4>
                <p>Automatic daily attendance summary</p>
              </div>
              <v-switch
                v-model="notificationSettings.dailyReports"
                color="warning"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>
          </div>
        </div>
      </div>

      <!-- 4. Security & Backup -->
      <div class="settings-card security">
        <div class="card-header">
          <div class="header-icon">
            <v-icon color="error" size="24">mdi-security</v-icon>
          </div>
          <div>
            <h3 class="card-title">Security & Backup</h3>
            <p class="card-subtitle">Data protection and system security settings</p>
          </div>
          <v-switch
            v-model="securitySettings.enabled"
            color="error"
            hide-details
            @change="markAsChanged"
          ></v-switch>
        </div>
        
        <div class="card-content" v-if="securitySettings.enabled">
          <div class="settings-grid">
            <div class="setting-group">
              <label class="setting-label">Data Retention (days)</label>
              <v-text-field
                v-model.number="securitySettings.dataRetentionDays"
                type="number"
                min="30"
                max="3650"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group">
              <label class="setting-label">Session Timeout (minutes)</label>
              <v-text-field
                v-model.number="securitySettings.sessionTimeout"
                type="number"
                min="5"
                max="480"
                variant="outlined"
                density="compact"
                hide-details
                @input="markAsChanged"
              ></v-text-field>
            </div>

            <div class="setting-group full-width">
              <label class="setting-label">Backup Frequency</label>
              <v-select
                v-model="securitySettings.backupFrequency"
                :items="backupFrequencyOptions"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markAsChanged"
              ></v-select>
            </div>
          </div>

          <div class="backup-actions">
            <v-btn
              variant="outlined"
              color="primary"
              prepend-icon="mdi-backup-restore"
              @click="initiateBackup"
              :loading="backupLoading"
            >
              Create Backup Now
            </v-btn>
            <v-btn
              variant="outlined"
              color="success"
              prepend-icon="mdi-download"
              @click="downloadLogs"
            >
              Download Access Logs
            </v-btn>
          </div>
        </div>
      </div>

      <!-- 5. Device & Location -->
      <div class="settings-card device">
        <div class="card-header">
          <div class="header-icon">
            <v-icon color="info" size="24">mdi-devices</v-icon>
          </div>
          <div>
            <h3 class="card-title">Device & Location</h3>
            <p class="card-subtitle">Manage devices and location restrictions</p>
          </div>
          <v-switch
            v-model="deviceSettings.enabled"
            color="info"
            hide-details
            @change="markAsChanged"
          ></v-switch>
        </div>
        
        <div class="card-content" v-if="deviceSettings.enabled">
          <div class="device-options">
            <div class="device-item">
              <div class="device-info">
                <h4>Location Restrictions</h4>
                <p>Require employees to be at specific location</p>
              </div>
              <v-switch
                v-model="deviceSettings.locationRestrictions"
                color="info"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>

            <div class="device-item">
              <div class="device-info">
                <h4>Camera Quality Check</h4>
                <p>Ensure minimum camera quality for face recognition</p>
              </div>
              <v-switch
                v-model="deviceSettings.cameraQualityCheck"
                color="info"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>

            <div class="device-item">
              <div class="device-info">
                <h4>Device Registration</h4>
                <p>Require device registration before first use</p>
              </div>
              <v-switch
                v-model="deviceSettings.deviceRegistration"
                color="info"
                hide-details
                @change="markAsChanged"
              ></v-switch>
            </div>
          </div>

          <div class="settings-grid" v-if="deviceSettings.cameraQualityCheck">
            <div class="setting-group">
              <label class="setting-label">Minimum Image Resolution</label>
              <v-select
                v-model="deviceSettings.minResolution"
                :items="resolutionOptions"
                variant="outlined"
                density="compact"
                hide-details
                @update:model-value="markAsChanged"
              ></v-select>
            </div>

            <div class="setting-group">
              <label class="setting-label">Image Quality Threshold</label>
              <div class="slider-container">
                <v-slider
                  v-model="deviceSettings.imageQualityThreshold"
                  min="0.1"
                  max="1.0"
                  step="0.1"
                  thumb-label
                  color="info"
                  @input="markAsChanged"
                >
                  <template v-slot:append>
                    <div class="slider-value">{{ (deviceSettings.imageQualityThreshold * 100).toFixed(0) }}%</div>
                  </template>
                </v-slider>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import '@/assets/css/SettingTab.css';
import { settingsApi } from '@/services/api';

export default {
  name: 'SettingsTab',
  setup() {
    const saving = ref(false);
    const backupLoading = ref(false);
    const hasChanges = ref(false);

    const timeSettings = ref({
      enabled: true,
      workStartTime: '08:30', workEndTime: '17:30',
      checkinStart: '07:00', checkinEnd: '09:00',
      lunchStart: '12:00', lunchEnd: '13:30',
      minWorkHours: 4,
      enableTimeValidation: true,
      allowWeekendWork: true,
      autoBreakDeduction: true,
      allowEarlyCheckout: false,
      strictTimeEnforcement: false
    });

    const policySettings = ref({
      enabled: true,
      maxCheckins: 1, maxCheckouts: 1,
      gracePeriod: 15, overtimeThreshold: 8
    });

    const notificationSettings = ref({
      enabled: true,
      adminAlerts: true, employeeReminders: true,
      systemHealth: true, dailyReports: false,
      enableEmailNotifications: false,
      enableLateArrivalAlert: true,
      enableAbsenteeAlert: true,
      enableOvertimeNotifications: true,
      absenteeAlertDelay: 2.0
    });

    const securitySettings = ref({
      enabled: true,
      dataRetentionDays: 365, sessionTimeout: 60,
      backupFrequency: 'daily', enableAuditLog: true
    });

    const deviceSettings = ref({
      enabled: true,
      locationRestrictions: false,
      cameraQualityCheck: true,
      deviceRegistration: false,
      minResolution: '720p', imageQualityThreshold: 0.7,
      enableLivenessDetection: true,
      enableMultipleFaceCheck: true
    });

    const backupFrequencyOptions = [
      { title: 'Daily', value: 'daily' },
      { title: 'Weekly', value: 'weekly' },
      { title: 'Monthly', value: 'monthly' }
    ];

    const resolutionOptions = [
      { title: '480p (640x480)', value: '480p' },
      { title: '720p (1280x720)', value: '720p' },
      { title: '1080p (1920x1080)', value: '1080p' }
    ];

    const hasUnsavedChanges = computed(() => hasChanges.value);
    const markAsChanged = () => { hasChanges.value = true; };

    const loadSettings = async () => {
      const res = await settingsApi.getSettings();
      if (res.success) {
        Object.assign(timeSettings.value, res.data.timeSettings);
        Object.assign(policySettings.value, res.data.policySettings);
        Object.assign(notificationSettings.value, res.data.notificationSettings);
        Object.assign(securitySettings.value, res.data.securitySettings);
        Object.assign(deviceSettings.value, res.data.deviceSettings);
        hasChanges.value = false;
      } else {
        alert(res.error);
      }
    };

    const saveAllSettings = async () => {
      saving.value = true;
      try {
        const payload = {
          timeSettings: timeSettings.value,
          policySettings: policySettings.value,
          notificationSettings: notificationSettings.value,
          securitySettings: securitySettings.value,
          deviceSettings: deviceSettings.value
        };
        const res = await settingsApi.updateSettings(payload);
        if (res.success) {
          hasChanges.value = false;
          alert('Settings saved successfully.');
        } else {
          alert(res.error);
        }
      } catch (err) {
        console.error('Failed to save settings:', err);
      } finally {
        saving.value = false;
      }
    };

    const resetAllSettings = async () => {
      const confirmReset = confirm("Reset all settings to default?");
      if (!confirmReset) return;

      const res = await settingsApi.resetSystem();
      if (res.success) {
        await loadSettings();
        alert(res.message);
      } else {
        alert(res.error);
      }
    };

    const initiateBackup = async () => {
      backupLoading.value = true;
      const res = await settingsApi.createBackup();
      if (res.success) {
        alert(res.message);
      } else {
        alert(res.error);
      }
      backupLoading.value = false;
    };

    const downloadLogs = () => {
      console.log('Downloading logs...');
    };

    onMounted(() => {
      loadSettings();
    });

    return {
      saving, backupLoading, hasUnsavedChanges,
      timeSettings, policySettings,
      notificationSettings, securitySettings,
      deviceSettings, backupFrequencyOptions,
      resolutionOptions, markAsChanged,
      saveAllSettings, resetAllSettings,
      initiateBackup, downloadLogs
    };
  }
};
</script>