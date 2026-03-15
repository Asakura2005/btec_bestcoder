<template>
  <div class="face-capture-overlay">
    <div class="face-capture-container">
      <div class="face-capture-header">
        <h2>Collecting facial data</h2>
        <p>Employee: <strong>{{ userId }}</strong></p>
      </div>

      <div class="face-capture-content">
        <div class="instructions-section">
          <h3>Collection instructions:</h3>
          <ul>
            <li>The system will collect 5 different facial images.</li>
            <li>Please follow the direction specified.</li>
            <li>Ensure that the lighting is sufficient and your face is clearly visible.</li>
            <li>Completion will be after collecting all 5 poses.</li>
          </ul>
        </div>

        <div class="video-container">
          <video ref="video" autoplay muted playsinline></video>
          <div class="video-overlay" v-if="!isTraining">
            <div class="overlay-content">
              <v-icon size="64" color="white">mdi-camera</v-icon>
              <p>Press "Start" to begin collecting facial data</p>
            </div>
          </div>
          <div class="video-overlay current-pose" v-if="isTraining && currentPose">
            <div class="overlay-content">
              <v-icon size="48" color="white">{{ getPoseIcon(currentPose) }}</v-icon>
              <p>{{ getPoseLabel(currentPose) }}</p>
              <v-progress-circular
                indeterminate
                color="white"
                size="24"
                width="3"
                class="mt-2"
              ></v-progress-circular>
            </div>
          </div>
        </div>

        <div class="progress-section">
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: (samplesCollected / totalSamples * 100) + '%' }"
            ></div>
          </div>
          <p class="progress-text">{{ samplesCollected }}/{{ totalSamples }} mẫu dữ liệu</p>
        </div>

        <div class="poses-grid" v-if="poses.length > 0">
          <div 
            v-for="(pose, index) in poses" 
            :key="pose"
            class="pose-item"
            :class="{
              'completed': index < currentPoseIndex,
              'current': index === currentPoseIndex,
              'pending': index > currentPoseIndex
            }"
          >
            <v-icon size="24" :color="getPoseItemColor(index)">
              {{ getPoseIcon(pose) }}
            </v-icon>
            <span>{{ getPoseLabel(pose) }}</span>
            <v-icon v-if="index < currentPoseIndex" size="16" color="success">
              mdi-check-circle
            </v-icon>
          </div>
        </div>

        <div class="controls">
          <v-btn
            :disabled="isTraining"
            color="primary"
            size="large"
            prepend-icon="mdi-camera"
            @click="startTraining"
            class="control-btn"
          >
            {{ isTraining ? 'Collecting data...' : 'Starting the collection' }}
          </v-btn>
          <v-btn
            :disabled="!isTraining"
            color="grey-darken-2"
            size="large"
            prepend-icon="mdi-stop"
            @click="stopTraining"
            class="control-btn"
          >
            Stop
          </v-btn>
          <v-btn
            color="grey-darken-2"
            size="large"
            prepend-icon="mdi-close"
            @click="closeCapture"
            class="control-btn"
          >
            Close
          </v-btn>
        </div>

        <div class="status-section" v-if="statusMessage">
          <v-alert
            :type="statusType"
            :text="statusMessage"
            class="status-alert"
          ></v-alert>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import '@/assets/css/FaceCapture.css';
import { captureFacePose, getRequiredPoses } from '@/services/api.js'
import { defineComponent, ref, onMounted, onUnmounted } from 'vue'

export default defineComponent({
  name: 'FaceCapture',
  props: {
    userId: {
      type: String,
      required: true
    }
  },
  emits: ['completed', 'cancelled'],
  setup(props, { emit }) {
    const video = ref(null)
    const stream = ref(null)
    const isTraining = ref(false)
    const poses = ref(['front', 'left', 'right', 'up', 'down'])
    const currentPoseIndex = ref(0)
    const samplesCollected = ref(0)
    const totalSamples = ref(5)
    const statusMessage = ref('')
    const statusType = ref('info')
    const captureTimeout = ref(null)

    const poseLabels = {
      front: 'Look straight into the camera',
      left: 'Turn your face to the left',
      right: 'Turn your face to the right',
      up: 'Look up',
      down: 'Look down'
    }

    const poseIcons = {
      front: 'mdi-face-man',
      left: 'mdi-arrow-left',
      right: 'mdi-arrow-right',
      up: 'mdi-arrow-up',
      down: 'mdi-arrow-down'
    }

    const currentPose = ref(null)

    const showStatus = (message, type = 'info') => {
      statusMessage.value = message
      statusType.value = type
      setTimeout(() => {
        statusMessage.value = ''
      }, 5000)
    }

    const getPoseLabel = (pose) => {
      return poseLabels[pose] || pose
    }

    const getPoseIcon = (pose) => {
      return poseIcons[pose] || 'mdi-face-man'
    }

    const getPoseItemColor = (index) => {
      if (index < currentPoseIndex.value) return 'success'
      if (index === currentPoseIndex.value) return 'primary'
      return 'grey'
    }

    const startCamera = async () => {
      try {
        stream.value = await navigator.mediaDevices.getUserMedia({ 
          video: true 
        })
        video.value.srcObject = stream.value
        await new Promise(resolve => {
          video.value.onloadedmetadata = resolve
        })
        return true
      } catch (error) {
        showStatus('Unable to access the camera: ' + error.message, 'error')
        return false
      }
    }

    const stopCamera = () => {
      if (stream.value) {
        stream.value.getTracks().forEach(track => track.stop())
        stream.value = null
      }
    }

    const captureFrame = async () => {
      if (!video.value) return null
      
      const canvas = document.createElement('canvas')
      canvas.width = video.value.videoWidth
      canvas.height = video.value.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video.value, 0, 0)
      
      return new Promise(resolve => {
        canvas.toBlob(resolve, 'image/jpeg', 0.9)
      })
    }

    const sendFaceData = async (pose, imageBlob) => {
        try {
            const formData = new FormData()
            formData.append('image', imageBlob, `${props.userId}_${pose}.jpg`)
            formData.append('employee_id', props.userId)
            formData.append('pose_type', pose)

            const response = await captureFacePose(formData)
            
            // Kiểm tra response structure
            if (!response.data) {
            throw new Error('Invalid response format')
            }

            // Kiểm tra success flag (nếu backend trả về)
            if (response.data.success === false) {
            throw new Error(response.data.error || 'Capture failed')
            }

            return response.data
            
        } catch (error) {
            console.error('Error sending face data:', error)
            
            // Xử lý different error types
            if (error.response?.status === 400) {
            throw new Error(error.response.data.error || error.response.data.message || 'Invalid request')
            } else if (error.response?.status === 404) {
            throw new Error('Employee not found')
            } else if (error.response?.status === 500) {
            throw new Error('Server error. Please try again later.')
            } else if (error.code === 'ECONNABORTED') {
            throw new Error('Connection timeout. Please try again.')
            } else {
            throw new Error(error.response?.data?.error || 'Network error')
            }
        }
    }

    const captureCurrentPose = async () => {
        if (!isTraining.value || currentPoseIndex.value >= poses.value.length) return

        const pose = poses.value[currentPoseIndex.value]
        currentPose.value = pose
        
        try {
            showStatus(`Preparing to capture the image ${getPoseLabel(pose)}...`, 'info')
            
            // Đợi một chút để người dùng chuẩn bị
            await new Promise(resolve => setTimeout(resolve, 2000))
            
            showStatus(`Capturing the image ${getPoseLabel(pose)}...`, 'info')
            
            const imageBlob = await captureFrame()
            if (!imageBlob) {
            throw new Error('Unable to capture the image')
            }

            const result = await sendFaceData(pose, imageBlob)
            
            // Validate result structure
            if (!result.pose_type || !result.progress) {
            throw new Error('Invalid response data')
            }
            
            samplesCollected.value++
            currentPoseIndex.value++
            
            showStatus(`Successfully collected ${getPoseLabel(pose)}!`, 'success')
            
            // Log progress for debugging
            console.log('Training progress:', result.progress)
            
            // Nếu chưa hoàn thành, tiếp tục với pose tiếp theo
            if (currentPoseIndex.value < poses.value.length) {
            captureTimeout.value = setTimeout(() => {
                captureCurrentPose()
            }, 2000)
            } else {
            // Hoàn thành tất cả poses
            finishTraining()
            }
            
        } catch (error) {
            console.error('Capture error:', error)
            showStatus(`Error during data collection ${getPoseLabel(pose)}: ${error.message}`, 'error')
            
            // Stop training on error
            isTraining.value = false
            currentPose.value = null
            
            // Clear timeout nếu có
            if (captureTimeout.value) {
            clearTimeout(captureTimeout.value)
            captureTimeout.value = null
            }
        }
    }

    const finishTraining = () => {
      isTraining.value = false
      currentPose.value = null
      showStatus('Facial data collection complete!!', 'success')
      
      setTimeout(() => {
        emit('completed')
      }, 2000)
    }

    const startTraining = async () => {
      if (isTraining.value) return

      const cameraStarted = await startCamera()
      if (!cameraStarted) return

      isTraining.value = true
      currentPoseIndex.value = 0
      samplesCollected.value = 0
      
      showStatus('Starting facial data collection...', 'info')
      
      // Đợi một chút rồi bắt đầu chụp
      setTimeout(() => {
        captureCurrentPose()
      }, 1000)
    }

    const stopTraining = () => {
      isTraining.value = false
      currentPose.value = null
      if (captureTimeout.value) {
        clearTimeout(captureTimeout.value)
        captureTimeout.value = null
      }
      showStatus('Data collection has been stopped', 'info')
    }

    const closeCapture = () => {
      stopTraining()
      stopCamera()
      emit('cancelled')
    }

    onMounted(() => {
      startCamera()
    })

    onUnmounted(() => {
      stopCamera()
      if (captureTimeout.value) {
        clearTimeout(captureTimeout.value)
      }
    })

    return {
      video,
      isTraining,
      poses,
      currentPoseIndex,
      samplesCollected,
      totalSamples,
      statusMessage,
      statusType,
      currentPose,
      getPoseLabel,
      getPoseIcon,
      getPoseItemColor,
      startTraining,
      stopTraining,
      closeCapture
    }
  }
})
</script>