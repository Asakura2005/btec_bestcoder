<template>
  <div class="container">
    <div class="background-decoration-top"></div>
    <div class="background-decoration-bottom"></div>

        <!-- Nút Admin Login -->
    <div class="admin-login-button">
      <v-btn
        class="logout-btn"
        variant="outlined"
        color="white"
        prepend-icon="mdi-shield-lock-outline"
        @click="$router.push('/login')"
      >
        User Login
      </v-btn>
    </div>

    <div class="main-content-wrapper">
      <div class="header">
        <div class="header-icon">
          <User />
        </div>
        <h1 class="header-title">Employee Attendance</h1>
        <p class="header-subtitle">Attendance Management System</p>
      </div>

      <div v-if="error" class="error-alert">
        <div class="error-content">
          <AlertCircle />
          <span>Error</span>
        </div>
        <p>{{ error }}</p>
      </div>

      <div class="card">
        <!-- Camera Section -->
        <div v-if="currentStep === 'camera'" class="section">
          <div class="camera-section">
            <Camera />
            <h2>Face Recognition</h2>
            <p>{{ statusMessage }}</p>
          </div>

          <div class="video-container">
            <div class="video-frame">
              <video ref="videoRef" autoplay playsinline muted></video>
              <canvas ref="canvasRef"></canvas>
              
              <div class="face-overlay">
                <div class="top-left"></div>
                <div class="top-right"></div>
                <div class="bottom-left"></div>
                <div class="bottom-right"></div>
              </div>
            </div>
            
            <div class="camera-controls">
              <v-btn
                v-if="isCameraActive"
                @click="stopWebcam"
                color="red-darken-2"
                size="large"
                prepend-icon="mdi-webcam-off"
                class="control-button"
              >
                Turn off Webcam
              </v-btn>
              <v-btn
                v-else
                @click="startCamera"
                color="green-darken-2"
                size="large"
                prepend-icon="mdi-webcam"
                class="control-button"
              >
                Turn on Webcam
              </v-btn>
            </div>
          </div>
        </div>

        <!-- Processing Section -->
        <div v-if="currentStep === 'processing'" class="section processing-section">
          <div class="processing-content">
            <div class="processing-icon">
              <RefreshCw class="animate-spin" />
            </div>
            <h2>Processing...</h2>
            <p>{{ statusMessage }}</p>
          </div>
          
          <div class="progress-bar">
            <div class="progress-fill"></div>
          </div>
        </div>

        <!-- Success Section -->
        <div v-if="currentStep === 'success' && employee" class="section">
          <div class="success-section">
            <div class="success-icon">
              <CheckCircle />
            </div>
            <h2>Check-{{ employee.status === 'check-in' ? 'in' : 'out' }} Successful!</h2>
            <p>Welcome back to the office</p>
          </div>

          <div class="employee-card">
            <div class="employee-info">
              <div class="employee-avatar">
                {{ employee.full_name.split(' ').map(n => n[0]).join('') }}
              </div>
              <div class="employee-details-text">
                <h3>{{ employee.full_name }}</h3>
                <p>ID: {{ employee.employee_id }}</p>
                <p>{{ employee.department }}</p>
              </div>
            </div>

            <div class="employee-details">
              <div class="detail-box">
                <Clock />
                <p>Time</p>
                <p>{{ formatTimestamp(employee.timestamp) }}</p>
              </div>
              <div class="detail-box">
                <Calendar />
                <p>Status</p>
                <p>{{ employee.status }}</p>
              </div>
            </div>
          </div>

          <div class="action-buttons">
            <v-btn
              @click="resetCamera"
              color="blue-grey-darken-1"
              size="large"
              prepend-icon="mdi-refresh"
              class="action-button"
            >
              New Check-in
            </v-btn>
            <v-btn
              @click="viewHistory"
              color="purple-darken-3"
              size="large"
              prepend-icon="mdi-history"
              class="action-button"
            >
              View History
            </v-btn>
          </div>

          <!-- History Section - Moved here, below success section -->
          <div v-if="showHistory" class="history-section">
            <div class="history-header">
              <h3>Recent Attendance History</h3>
              <button @click="showHistory = false" class="close-history-button">
                <RefreshCw />
              </button>
            </div>

            <div class="history-list">
              <div
                v-for="(record, index) in attendanceHistory"
                :key="index"
                class="history-item"
              >
                <div class="history-details">
                  <div class="history-icon">
                    <Calendar />
                  </div>
                  <div class="history-info">
                    <p class="history-date">{{ formatHistoryDate(record.date) }}</p>
                    <p class="history-time">
                      In: {{ record.check_in || 'N/A' }} • Out: {{ record.check_out || 'N/A' }}
                    </p>
                  </div>
                </div>
                <span :class="getStatusBadge(record.status)">
                  {{ record.status }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Standalone History Section (when accessed directly) -->
        <div v-if="showHistory && currentStep !== 'success'" class="section">
          <div class="history-header">
            <h2>Attendance History</h2>
            <button @click="showHistory = false" class="refresh-button">
              <RefreshCw />
            </button>
          </div>

          <div class="history-list">
            <div
              v-for="(record, index) in attendanceHistory"
              :key="index"
              class="history-item"
            >
              <div class="history-details">
                <div class="history-icon">
                  <Calendar />
                </div>
                <div class="history-info">
                  <p class="history-date">{{ formatHistoryDate(record.date) }}</p>
                  <p class="history-time">
                    In: {{ record.check_in || 'N/A' }} • Out: {{ record.check_out || 'N/A' }}
                  </p>
                </div>
              </div>
              <span :class="getStatusBadge(record.status)">
                {{ record.status }}
              </span>
            </div>
          </div>

          <div class="history-footer">
            <button @click="showHistory = false" class="back-button">
              Back to Check-in
            </button>
          </div>
        </div>
      </div>

      <div class="footer">
        <p>© 2025 Employee Management System. All rights reserved.</p>
      </div>
    </div>
  </div>
</template>

<script>
import '@/assets/css/Attendance.css';
import { Camera, User, Clock, Calendar, History, CheckCircle, AlertCircle, RefreshCw } from 'lucide-vue-next';
import { recognizeFace, getAttendanceHistory } from '../services/api';
import { v4 as uuidv4 } from 'uuid';

export default {
  name: 'AttendanceInterface',
  components: {
    Camera,
    User,
    Clock,
    Calendar,
    History,
    CheckCircle,
    AlertCircle,
    RefreshCw
  },
  data() {
    return {
      currentStep: 'camera',
      isProcessing: false,
      employee: null,
      attendanceRecord: null,
      attendanceHistory: [],
      error: '',
      showHistory: false,
      stream: null,
      recognitionInterval: null,
      isCameraActive: false,
      sessionId: null,
      statusMessage: "Scanning for your face, please look directly at the camera.",
    };
  },
  watch: {
    currentStep(newVal) {
      if (newVal === 'camera') {
        this.startCamera();
      } else {
        this.stopContinuousRecognition();
      }
    }
  },
  mounted() {
    this.startCamera();
  },
  beforeUnmount() {
    this.stopContinuousRecognition();
  },
  methods: {
    formatTimestamp(timestamp) {
      if (!timestamp) return 'N/A';
      try {
        let date;
        
        // Check if timestamp is already in DD/MM/YYYY HH:mm:ss format
        if (typeof timestamp === 'string' && timestamp.includes('/')) {
          // Parse DD/MM/YYYY HH:mm:ss format
          const parts = timestamp.split(' ');
          if (parts.length === 2) {
            const datePart = parts[0]; // "13/07/2025"
            const timePart = parts[1]; // "23:55:47"
            
            const dateComponents = datePart.split('/');
            if (dateComponents.length === 3) {
              const day = dateComponents[0];
              const month = dateComponents[1];
              const year = dateComponents[2];
              
              // Create date in MM/DD/YYYY format for JavaScript Date constructor
              const jsDateString = `${month}/${day}/${year} ${timePart}`;
              date = new Date(jsDateString);
            }
          }
        } else {
          // Try parsing as ISO string or other formats
          date = new Date(timestamp);
        }
        
        if (!date || isNaN(date.getTime())) {
          console.error('Invalid date:', timestamp);
          return timestamp; // Return original if parsing fails
        }
        
        return date.toLocaleString('en-US', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
          hour12: false
        });
      } catch (error) {
        console.error('Error formatting timestamp:', error);
        return timestamp; // Return original if error occurs
      }
    },
    
formatHistoryDate(dateString) {
  if (!dateString) return 'N/A';
  try {
    let date;
    
    // Check if dateString is in YYYY-MM-DD format (from our historyMap)
    if (typeof dateString === 'string' && dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
      date = new Date(dateString + 'T00:00:00'); // Add time to avoid timezone issues
    } 
    // Check if dateString is in DD/MM/YYYY format
    else if (typeof dateString === 'string' && dateString.includes('/')) {
      const parts = dateString.split('/');
      if (parts.length === 3) {
        const day = parts[0];
        const month = parts[1];
        const year = parts[2];
        
        // Create date in MM/DD/YYYY format for JavaScript Date constructor
        const jsDateString = `${month}/${day}/${year}`;
        date = new Date(jsDateString);
      }
    } else {
      date = new Date(dateString);
    }
    
    if (!date || isNaN(date.getTime())) {
      console.error('Invalid date:', dateString);
      return dateString; // Return original if parsing fails
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (error) {
    console.error('Error formatting history date:', error);
    return dateString; // Return original if error occurs
  }
},

    async startCamera() {
      try {
        const mediaStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'user' }
        });
        this.stream = mediaStream;
        if (this.$refs.videoRef) {
          this.$refs.videoRef.srcObject = mediaStream;
        }
        this.isCameraActive = true;
        this.statusMessage = "Scanning for your face, please look directly at the camera.";
        this.startContinuousRecognition();
      } catch (err) {
        this.error = 'Cannot access camera. Please check permissions.';
        this.isCameraActive = false;
        this.statusMessage = "Camera access denied or unavailable.";
      }
    },

    startContinuousRecognition() {
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval);
      }
      this.sessionId = uuidv4();
      if (this.isCameraActive) {
        this.recognitionInterval = setInterval(this.sendFrameForRecognition, 3000);
      }
    },

    stopContinuousRecognition() {
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval);
        this.recognitionInterval = null;
      }
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
      }
      this.isCameraActive = false;
      if (this.$refs.videoRef) {
        this.$refs.videoRef.srcObject = null;
      }
      this.sessionId = null;
      this.statusMessage = "Webcam turned off. Ready to start new recognition.";
    },

    stopWebcam() {
      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
      }
      if (this.$refs.videoRef) {
        this.$refs.videoRef.srcObject = null;
      }
      this.isCameraActive = false;
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval);
        this.recognitionInterval = null;
      }
      this.sessionId = null;
      console.log('Webcam is already turn off.');
      this.currentStep = 'camera';
      this.isProcessing = false;
      this.error = '';
      this.statusMessage = "Webcam turned off. Ready to start new recognition.";
    },

    // Sửa logic xử lý response trong sendFrameForRecognition()
    async sendFrameForRecognition() {
      if (this.isProcessing || this.currentStep !== 'camera') {
        return;
      }

      if (!this.$refs.videoRef || !this.$refs.canvasRef) {
        this.error = 'Camera or canvas not ready.';
        this.isProcessing = false;
        return;
      }

      this.isProcessing = true;
      this.error = '';

      const canvas = this.$refs.canvasRef;
      const video = this.$refs.videoRef;
      const context = canvas.getContext('2d');

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0);

      try {
        const base64Image = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
        const response = await recognizeFace({ 
          base64_image: base64Image, 
          session_id: this.sessionId 
        });

        console.log('API Response:', response);

        // Xử lý response thành công (attendance recorded)
        if (response.success && response.message === 'Attendance recorded successfully') {
          if (response.employee && response.employee.full_name) {
            this.employee = {
              employee_id: response.employee.employee_id,
              full_name: response.employee.full_name,
              department: response.employee.department,
              timestamp: response.timestamp,
              status: response.status
            };
            
            this.attendanceRecord = {
              status: response.status,
              attendance_type: response.attendance_type,
              timestamp: response.timestamp
            };
            
            this.stopContinuousRecognition();
            this.currentStep = 'success';
            this.statusMessage = "Check-in Successful!";
            return;
          } else {
            this.error = 'Recognition successful but employee data is missing';
            this.statusMessage = this.error;
          }
        }
        
        // Xử lý liveness detection đang diễn ra
        else if (response.success === false && response.liveness_passed === false) {
          // Đang trong quá trình liveness check
          this.statusMessage = response.message || "Performing liveness check...";
          this.currentStep = 'camera';
        }
        
        // Xử lý face recognition failed
        else if (response.success === false) {
          this.error = response.message || 'Face recognition failed';
          this.statusMessage = this.error;
          this.currentStep = 'camera';
        }
        
        // Fallback cho các trường hợp khác
        else {
          this.statusMessage = response.message || "Processing...";
          this.currentStep = 'camera';
        }
        
      } catch (err) {
        console.error('Recognition error:', err);
        this.error = err.response?.data?.message || err.response?.data?.error || 'Network error occurred';
        this.statusMessage = this.error;
        this.currentStep = 'camera';
      } finally {
        // Đảm bảo luôn reset isProcessing
        this.isProcessing = false;
      }
    },

    // Tăng session timeout và giảm frequency
    startContinuousRecognition() {
      if (this.recognitionInterval) {
        clearInterval(this.recognitionInterval);
      }
      this.sessionId = uuidv4();
      if (this.isCameraActive) {
        // Tăng interval lên 4 giây để tránh timeout
        this.recognitionInterval = setInterval(this.sendFrameForRecognition, 4000);
      }
    },

    async viewHistory() {
      try {
        if (!this.employee || !this.employee.employee_id) {
          this.error = 'Unable to view history: No employee information detected.';
          return;
        }

        const employeeIdToFetch = this.employee.employee_id;
        const response = await getAttendanceHistory(employeeIdToFetch);
        
        const historyMap = {};
        
        response.records.forEach(record => {
          let date;
          let timeString;
          
          // Parse timestamp từ backend (có thể là DD/MM/YYYY HH:mm:ss)
          if (record.timestamp) {
            if (typeof record.timestamp === 'string' && record.timestamp.includes('/')) {
              // Parse DD/MM/YYYY HH:mm:ss format
              const parts = record.timestamp.split(' ');
              if (parts.length >= 2) {
                const datePart = parts[0]; // "13/07/2025"
                const timePart = parts[1]; // "21:04:37"
                
                const dateComponents = datePart.split('/');
                if (dateComponents.length === 3) {
                  const day = dateComponents[0];
                  const month = dateComponents[1];
                  const year = dateComponents[2];
                  
                  // Create date in MM/DD/YYYY format for JavaScript Date constructor
                  const jsDateString = `${month}/${day}/${year} ${timePart}`;
                  date = new Date(jsDateString);
                  
                  // Use the time part directly from the timestamp
                  timeString = timePart;
                }
              }
            } else {
              // Try parsing as ISO string or other formats
              date = new Date(record.timestamp);
              timeString = date.toLocaleTimeString('en-US', { 
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
              });
            }
          }
          
          // Fallback to current date if parsing fails
          if (!date || isNaN(date.getTime())) {
            console.error('Invalid timestamp in record:', record.timestamp);
            date = new Date(); // Use current date as fallback
            timeString = "00:00:00"; // Default time if parsing fails
          }
          
          // Format date as YYYY-MM-DD for consistency
          const dateKey = date.toLocaleDateString('en-CA'); // This returns YYYY-MM-DD format
          
          if (!historyMap[dateKey]) {
            historyMap[dateKey] = { 
              date: dateKey, 
              check_in: null, 
              check_out: null, 
              status: 'Absent' 
            };
          }
          
          if (record.status === 'check-in') {
            historyMap[dateKey].check_in = timeString;
            historyMap[dateKey].status = record.attendance_type === 'late' ? 'Late' : 'Present';
          } else if (record.status === 'check-out') {
            historyMap[dateKey].check_out = timeString;
          }
        });

        this.attendanceHistory = Object.values(historyMap)
          .sort((a, b) => new Date(b.date) - new Date(a.date))
          .slice(0, 10);
        
        this.showHistory = true;
        
      } catch (err) {
        console.error('Error loading attendance history:', err);
        this.error = err.response?.data?.error || 'Failed to load attendance history.';
      }
    },

    resetCamera() {
      this.currentStep = 'camera';
      this.employee = null;
      this.attendanceRecord = null;
      this.error = '';
      this.showHistory = false;
      this.statusMessage = "Scanning for your face, please look directly at the camera.";
    },

    getStatusBadge(status) {
      switch (status) {
        case 'Present': return 'badge badge-present';
        case 'Late': return 'badge badge-late';
        case 'Absent': return 'badge badge-absent';
        default: return 'badge badge-default';
      }
    }
  }
};
</script>