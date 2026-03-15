// src/services/api/recovery.js
import api from './index'

// Admin APIs
export const getPendingRecoveryRequests = async () => {
  try {
    console.log('Get pending recovery requests')
    const response = await api.get('/api/admin/attendance/recovery/pending')
    return response.data.pending_requests
  } catch (error) {
    console.error('Get pending recovery requests error:', error.response?.data || error.message)
    throw error
  }
}

export const processRecoveryRequest = async ({ request_id, approved, reason }) => {
  try {
    const requestBody = {
      status: approved ? 'approved' : 'rejected',  
      notes: reason,  
    };
    
    const response = await api.post(`/api/admin/attendance/recovery/process/${request_id}`, requestBody)
    return response.data

  } catch (error) {
    console.error('Process recovery error details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      requestData: error.config?.data
    });
    throw error
  }
}

export const getAllRecoveryRequests = async () => {
  try {
    console.log('Get all recovery requests')
    const response = await api.get('/api/admin/attendance/recovery/all')
    return response.data.requests
  } catch (error) {
    console.error('Get all recovery requests error:', error.response?.data || error.message)
    throw error
  }
}

// Employee APIs
export const submitEmployeeRecoveryRequest = async (data) => {
  try {
    console.log('Submitting employee recovery request:', data);
    const response = await api.post('/api/employee/attendance/recovery/submit', data); 
    console.log('Employee recovery request submitted successfully:', response.data);
    return response.data;
  } catch (error) {
    console.error('Error submitting employee recovery request:', error.response?.data || error.message);
    throw error;
  }
};

export const getEmployeeRecoveryRequests = async () => {
  try {
    console.log('Get employee recovery requests');
    const response = await api.get('/api/employee/attendance/recovery/my-requests'); 
    console.log('Employee recovery requests fetched successfully:', response.data);
    return response.data.requests;
  } catch (error) {
    console.error('Error fetching employee recovery requests:', error.response?.data || error.message);
    throw error;
  }
};