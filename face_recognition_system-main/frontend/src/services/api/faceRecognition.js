// src/services/api/faceRecognition.js
import api from './index'

// Nhận diện khuôn mặt
export const recognizeFace = async (formData) => {
  try {
    console.log('📷 Face recognition request')
    
    const response = await api.post('/api/recognize', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    
    console.log('Face recognition success:', response.data)
    return response.data
    
  } catch (error) {
    console.error('Face recognition error:', error.response?.data || error.message)
    throw error
  }
}

// Gửi ảnh training
export const captureFacePose = (data) => {
  return api.post('/api/face-training/capture', data, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
}

// Lấy danh sách pose cần thiết
export const getRequiredPoses = () => {
  return Promise.resolve(['front', 'left', 'right', 'up', 'down']);
}