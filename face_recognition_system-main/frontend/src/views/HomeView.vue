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
            <div v-if="currentTab === 'dashboard'" class="content-panel">
              <DashboardTab />
            </div>

            <div v-else-if="currentTab === 'employee-management'" class="content-panel">
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

            <div v-else-if="currentTab === 'payroll'" class="content-panel">
              <PayrollTab/>
            </div>
          </transition>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import '@/assets/css/Login.css';
import '@/assets/css/HomeView.css';
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import DashboardTab from '@/components/DashboardTab.vue';
import EmployeeManagementTab from '@/components/EmployeeManagementTab.vue';
import AttendanceHistoryTab from '@/components/AttendanceHistoryTab.vue';
import AttendanceRecoveryRequestTab from '@/components/AttendanceRecoveryRequestTab.vue';
import SettingTab from '@/components/SettingTab.vue';
import PayrollTab from '@/components/PayrollTab.vue';

export default {
  name: 'AdminDashboard',
  components: {
    DashboardTab,
    EmployeeManagementTab,
    AttendanceHistoryTab,
    SettingTab,
    AttendanceRecoveryRequestTab,
    PayrollTab
  },
  setup() {
    const currentTab = ref('dashboard');
    const router = useRouter();
    const authStore = useAuthStore();
    const pendingRequestsCount = ref(0);

    const tabs = [
      {
        value: 'dashboard',
        label: 'Dashboard',
        icon: 'mdi-view-dashboard'
      },
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
      },
      {
        value: 'payroll',
        label: 'Payroll',
        icon: 'mdi-cash-multiple'
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
/* Only unique overrides that aren't in HomeView.css */
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
</style>