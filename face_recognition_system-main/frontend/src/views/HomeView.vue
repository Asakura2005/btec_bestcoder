<!-- src/views/HomeView.vue -->
<template>
  <div class="admin-dashboard">
    <!-- Background Elements -->
    <div class="bg-gradient"></div>
    <div class="bg-pattern"></div>
    
    <!-- Header -->
    <header class="admin-header">
      <div class="header-content">
        <div class="brand-section">
          <div class="brand-icon">
            <v-icon size="40" color="white">mdi-cog-outline</v-icon>
          </div>
          <div class="brand-text">
            <h1 class="brand-title">Admin Portal</h1>
            <p class="brand-subtitle">Employee Management & System Overview</p>
          </div>
        </div>
        
        <v-btn
          class="logout-btn"
          variant="outlined"
          color="white"
          prepend-icon="mdi-logout"
          @click="handleLogout"
        >
          Logout
        </v-btn>
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
            <!-- Badge for pending requests -->
            <v-badge 
              v-if="tab.value === 'audit-logs' && pendingRequestsCount > 0"
              :content="pendingRequestsCount"
              color="error"
              class="tab-badge"
              inline
            >
            </v-badge>
          </button>
        </div>

        <!-- Content Area -->
        <div class="content-area">
          <transition name="fade" mode="out-in">
            <div v-if="currentTab === 'employee-management'" class="content-panel">
              <EmployeeManagementTab />
            </div>

            <div v-else-if="currentTab === 'attendance-history'" class="content-panel">
              <AttendanceHistoryTab />
            </div>

            <div v-else-if="currentTab === 'audit-logs'" class="content-panel">
              <AttendanceRecoveryRequestTab @pending-count-updated="updatePendingCount" />
            </div>

            <div v-else-if="currentTab === 'settings'" class="content-panel">
              <SettingTab/>
            </div>
          </transition>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import '@/assets/css/Login.css';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import EmployeeManagementTab from '@/components/EmployeeManagementTab.vue';
import AttendanceHistoryTab from '@/components/AttendanceHistoryTab.vue';
import AttendanceRecoveryRequestTab from '@/components/AttendanceRecoveryRequestTab.vue';
import SettingTab from '@/components/SettingTab.vue';

export default {
  name: 'AdminDashboard',
  components: {
    EmployeeManagementTab,
    AttendanceHistoryTab,
    SettingTab,
    AttendanceRecoveryRequestTab
  },
  setup() {
    const currentTab = ref('employee-management');
    const router = useRouter();
    const authStore = useAuthStore();
    const pendingRequestsCount = ref(0);

    const tabs = [
      {
        value: 'employee-management',
        label: 'Employee Management',
        icon: 'mdi-account-group'
      },
      {
        value: 'attendance-history',
        label: 'Attendance History',
        icon: 'mdi-calendar-clock'
      },
      {
        value: 'audit-logs',
        label: 'Attendance Recovery Request',
        icon: 'mdi-format-list-bulleted-square'
      },
      {
        value: 'settings',
        label: 'Settings',
        icon: 'mdi-tools'
      }
    ];

    const updatePendingCount = (count) => {
      pendingRequestsCount.value = count;
    };

    const handleLogout = async () => {
      try {
        await authStore.logout();
        router.push('/login');
        console.log('Admin logged out successfully.');
      } catch (error) {
        console.error('Logout error:', error);
        // Vẫn redirect về login dù có lỗi
        router.push('/login');
      }
    };

    return {
      currentTab,
      tabs,
      handleLogout,
      pendingRequestsCount,
      updatePendingCount
    };
  },
};
</script>

<style scoped>
/* Base Layout */
.admin-dashboard {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafc;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  overflow: hidden;
}

/* Background Elements */
.bg-gradient {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 320px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  z-index: 1;
}

/* Header */
.admin-header {
  position: relative;
  z-index: 10;
  padding: 40px 40px;
  background: transparent;
}

.brand-icon {
  width: 64px;
  height: 64px;
  background: rgba(255,255,255,0.15);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(12px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
}

.brand-title {
  font-size: 32px;
  font-weight: 800;
  margin: 0;
  line-height: 1.1;
  letter-spacing: -0.02em;
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Navigation Tabs */
.nav-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 35px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  padding: 10px;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1);
  border: 1px solid rgba(255,255,255,0.5);
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 24px;
  border: none;
  background: transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  color: #475569; /* Slate 600 */
  min-width: 200px;
  justify-content: center;
}

.nav-tab:hover {
  background: #f1f5f9;
  color: #1e293b;
  transform: translateY(-1px);
}

.nav-tab.active {
  background: #4f46e5;
  color: white;
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.35);
}

.tab-label {
  font-size: 15px;
  font-weight: 600;
}

/* Tab Badge Styling */
.tab-badge {
  position: absolute !important;
  top: 8px !important;
  right: 8px !important;
  z-index: 10;
}

.tab-badge :deep(.v-badge__badge) {
  font-size: 11px !important;
  min-width: 18px !important;
  height: 18px !important;
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.7);
  }
  70% {
    transform: scale(1.1);
    box-shadow: 0 0 0 6px rgba(244, 67, 54, 0);
  }
  100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(244, 67, 54, 0);
  }
}

/* Content Area */
.content-area {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 40px;
}

.content-panel {
  background: white;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-title {
  padding: 30px 30px 0 30px;
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}

.panel-content {
  flex: 1;
  padding: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-content {
  text-align: center;
  max-width: 400px;
}

.placeholder-icon {
  opacity: 0.3;
  margin-bottom: 20px;
}

.placeholder-content h3 {
  font-size: 20px;
  font-weight: 600;
  color: #334155;
  margin: 0 0 12px 0;
}

.placeholder-content p {
  color: #64748b;
  margin: 0;
  line-height: 1.6;
}

/* Transitions */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* Responsive Design */
@media (max-width: 768px) {
  .admin-header {
    padding: 20px 20px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .brand-section {
    flex-direction: column;
    gap: 15px;
  }
  
  .brand-title {
    font-size: 24px;
  }
  
  .brand-subtitle {
    font-size: 14px;
  }
  
  .content-container {
    padding: 0 20px;
  }
  
  .nav-tabs {
    flex-direction: column;
    gap: 4px;
  }
  
  .nav-tab {
    min-width: auto;
    width: 100%;
  }
  
  .panel-title {
    padding: 20px 20px 0 20px;
    font-size: 20px;
  }
  
  .panel-content {
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .admin-header {
    padding: 15px 15px;
  }
  
  .content-container {
    padding: 0 15px;
  }
  
  .brand-title {
    font-size: 20px;
  }
  
  .brand-subtitle {
    font-size: 13px;
  }
  
  .nav-tab {
    padding: 12px 16px;
  }
  
  .tab-label {
    font-size: 13px;
  }
}

/* Large screens */
@media (min-width: 1400px) {
  .nav-tabs {
    justify-content: center;
  }
  
  .nav-tab {
    min-width: 220px;
  }
}
</style>