<template>
  <div class="attendance-recovery-tab">
    <h2 class="panel-title">Attendance Recovery Requests</h2>
    <div class="panel-content">
      <v-card class="elevation-6 rounded-xl pa-4">
        <v-card-title class="d-flex align-center justify-space-between mb-4">
          <span class="text-h5 font-weight-bold text-blue-grey-darken-3">All Requests</span>
          <v-btn 
            color="primary" 
            prepend-icon="mdi-refresh" 
            @click="fetchAllRequests" 
            :loading="loading"
            variant="flat"
            class="rounded-lg"
          >
            Refresh
          </v-btn>
        </v-card-title>
        
        <v-card-text>
          <v-alert
            v-if="errorMessage"
            type="error"
            closable
            class="mb-4"
            variant="tonal"
            density="compact"
          >
            {{ errorMessage }}
          </v-alert>

          <v-data-table
            :headers="headers"
            :items="allRequests"
            :loading="loading"
            class="elevation-0 rounded-lg"
            no-data-text="No attendance recovery requests found."
          >
            <template v-slot:item.requested_at="{ item }">
              {{ formatDateTime(item.requested_at) }}
            </template>
            <template v-slot:item.request_date="{ item }">
              {{ formatDate(item.request_date) }}
            </template>
            <template v-slot:item.approved_at="{ item }">
              {{ item.approved_at ? formatDateTime(item.approved_at) : '-' }}
            </template>
            <template v-slot:item.admin_username="{ item }">
              {{ item.admin_username || '-' }}
            </template>
            <template v-slot:item.status="{ item }">
              <v-chip 
                :color="getStatusColor(item.status)" 
                variant="flat" 
                size="small"
                class="rounded-lg"
              >
                {{ getStatusText(item.status) }}
              </v-chip>
            </template>
            <template v-slot:item.actions="{ item }">
              <div class="d-flex gap-2" v-if="item.status === 'pending'">
                <v-btn 
                  color="success" 
                  variant="flat" 
                  size="small" 
                  class="rounded-lg"
                  @click="confirmProcessRequest(item, 'approved')"
                  prepend-icon="mdi-check-circle"
                >
                  Approve
                </v-btn>
                <v-btn 
                  color="error" 
                  variant="flat" 
                  size="small" 
                  class="rounded-lg"
                  @click="confirmProcessRequest(item, 'rejected')"
                  prepend-icon="mdi-close-circle"
                >
                  Reject
                </v-btn>
              </div>
              <span v-else class="text-grey">{{ getStatusText(item.status) }}</span>
            </template>
            <template v-slot:no-data>
              <v-alert type="info" variant="tonal" class="my-4">
                No attendance recovery requests found.
              </v-alert>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </div>

    <v-dialog v-model="dialogConfirm" max-width="500px">
      <v-card class="rounded-xl">
        <v-card-title class="text-h5 text-center pt-5">Confirm Action</v-card-title>
        <v-card-text class="text-center">
          Are you sure you want to {{ actionType }} this request from 
          <span class="font-weight-bold">{{ selectedRequest?.employee_name }} ({{ selectedRequest?.employee_id }})</span> 
          for <span class="font-weight-bold">{{ formatDate(selectedRequest?.request_date) }}</span>?
          <v-textarea
            v-model="adminNotes"
            label="Admin Notes (Optional)"
            rows="3"
            class="mt-4"
            variant="outlined"
            density="compact"
          ></v-textarea>
        </v-card-text>
        <v-card-actions class="justify-center pb-5">
          <v-btn color="grey-darken-1" variant="outlined" @click="dialogConfirm = false" class="rounded-lg">Cancel</v-btn>
          <v-btn 
            :color="actionType === 'approved' ? 'success' : 'error'" 
            variant="flat" 
            @click="processRequest" 
            :loading="processing"
            class="rounded-lg"
          >
            {{ actionType === 'approved' ? 'Approve' : 'Reject' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="snackbar.timeout"
      location="bottom right"
    >
      {{ snackbar.message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, defineExpose, defineEmits, watch } from 'vue';
import { processRecoveryRequest, getAllRecoveryRequests } from '@/services/api'
import { useAuthStore } from '@/stores/auth'; 
import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import '@/assets/css/AttendanceRecoveryRequestTab.css';

const authStore = useAuthStore();
dayjs.extend(customParseFormat)

// Define emits
const emit = defineEmits(['pending-count-updated']);

const headers = [
  { title: 'Employee ID', key: 'employee_id', sortable: true },
  { title: 'Full Name', key: 'employee_name', sortable: true },
  { title: 'Request Date', key: 'request_date', sortable: true },
  { title: 'Requested At', key: 'requested_at', sortable: true },
  { title: 'Reason', key: 'reason', sortable: false },
  { title: 'Status', key: 'status', sortable: true },  
  { title: 'Admin', key: 'admin_username', sortable: true },  
  { title: 'Approved At', key: 'approved_at', sortable: true }, 
  { title: 'Actions', key: 'actions', sortable: false },
];

const allRequests = ref([]);
const loading = ref(false);
const errorMessage = ref('');
const dialogConfirm = ref(false);
const selectedRequest = ref(null);
const actionType = ref(''); // 'approved' or 'rejected'
const adminNotes = ref('');
const processing = ref(false);

const snackbar = ref({
  show: false,
  message: '',
  color: '',
  timeout: 3000,
});

// Computed property để tính toán số lượng yêu cầu đang chờ xử lý
const pendingCount = computed(() => {
  return allRequests.value.filter(request => request.status === 'pending').length;
});

const fetchAllRequests = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const response = await getAllRecoveryRequests(); 
    allRequests.value = response;
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Failed to fetch all requests.';
  } finally {
    loading.value = false;
  }
};

const confirmProcessRequest = (request, type) => {
  selectedRequest.value = request;
  actionType.value = type;
  adminNotes.value = ''; // Reset notes
  dialogConfirm.value = true;
};

const processRequest = async () => {
  if (!selectedRequest.value) return;

  processing.value = true;
  errorMessage.value = '';
  try {
    const requestData = {
      request_id: selectedRequest.value.request_id,
      approved: actionType.value === 'approved',
      reason: adminNotes.value || 'No note provided',
    };

    const response = await processRecoveryRequest(requestData);

    snackbar.value = { show: true, message: response.message, color: 'success' };
    dialogConfirm.value = false;
    fetchAllRequests(); // Refresh list
    
  } catch (error) {
    errorMessage.value = error.response?.data?.error || 'Failed to process request.';
    snackbar.value = { show: true, message: errorMessage.value, color: 'error' };
  } finally {
    processing.value = false;
  }
};

// Helper for date formatting
const formatDateTime = (input) => {
  if (!input) return '';
  const parsed = dayjs(input, 'DD/MM/YYYY HH:mm:ss');
  return parsed.isValid() ? parsed.format('DD/MM/YYYY HH:mm:ss') : 'Invalid Date';
};

const formatDate = (input) => {
  if (!input) return '';
  const parsed = dayjs(input, ['DD/MM/YYYY', 'YYYY-MM-DD']);
  return parsed.isValid() ? parsed.format('DD/MM/YYYY') : 'Invalid Date';
};

const getStatusColor = (status) => {
  switch (status) {
    case 'pending':
      return 'warning';
    case 'approved':
      return 'success';
    case 'rejected':
      return 'error';
    default:
      return 'grey';
  }
};

const getStatusText = (status) => {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'approved':
      return 'Approved';
    case 'rejected':
      return 'Rejected';
    default:
      return status;
  }
};

onMounted(() => {
  fetchAllRequests();
});

// Expose pendingCount để component cha có thể access
defineExpose({
  pendingCount
});

// Watch pendingCount và emit event khi thay đổi
watch(pendingCount, (newCount) => {
  emit('pending-count-updated', newCount);
}, { immediate: true });
</script>

<style scoped>
.notification-badge {
  animation: none;
}

.pulse-animation {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.8;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.panel-title {
  position: relative;
}
</style>