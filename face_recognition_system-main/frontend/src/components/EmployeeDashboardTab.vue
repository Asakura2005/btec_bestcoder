<template>
  <div class="emp-dashboard">
    <div v-if="loading" class="loading-overlay">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <div v-else-if="data">
      <!-- Welcome & Status -->
      <div class="welcome-section">
        <div class="welcome-text">
          <h2>Welcome, {{ data.employee?.full_name }}</h2>
          <p>{{ data.employee?.department }} · {{ data.employee?.position }}</p>
        </div>
        <div :class="['today-badge', todayStatusClass]">
          <v-icon size="18" color="white">{{ todayStatusIcon }}</v-icon>
          <span>{{ todayStatusText }}</span>
        </div>
      </div>

      <!-- Personal Stat Cards -->
      <div class="emp-stat-cards">
        <div class="emp-stat-card">
          <div class="emp-stat-icon" style="background: linear-gradient(135deg, #10b981, #059669)">
            <v-icon size="24" color="white">mdi-calendar-check</v-icon>
          </div>
          <div class="emp-stat-info">
            <span class="emp-stat-value">{{ data.month_stats?.work_days || 0 }}</span>
            <span class="emp-stat-label">Work Days</span>
          </div>
          <span class="emp-stat-sub">/ {{ data.month_stats?.working_days_total || 0 }}</span>
        </div>

        <div class="emp-stat-card">
          <div class="emp-stat-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706)">
            <v-icon size="24" color="white">mdi-clock-alert</v-icon>
          </div>
          <div class="emp-stat-info">
            <span class="emp-stat-value">{{ data.month_stats?.late_count || 0 }}</span>
            <span class="emp-stat-label">Late Days</span>
          </div>
        </div>

        <div class="emp-stat-card">
          <div class="emp-stat-icon" style="background: linear-gradient(135deg, #ef4444, #dc2626)">
            <v-icon size="24" color="white">mdi-account-off</v-icon>
          </div>
          <div class="emp-stat-info">
            <span class="emp-stat-value">{{ data.month_stats?.absent_days || 0 }}</span>
            <span class="emp-stat-label">Absent Days</span>
          </div>
        </div>

        <div class="emp-stat-card">
          <div class="emp-stat-icon" style="background: linear-gradient(135deg, #6366f1, #4f46e5)">
            <v-icon size="24" color="white">mdi-percent</v-icon>
          </div>
          <div class="emp-stat-info">
            <span class="emp-stat-value">{{ data.month_stats?.attendance_rate || 0 }}%</span>
            <span class="emp-stat-label">Attendance Rate</span>
          </div>
        </div>
      </div>

      <!-- Trend Chart -->
      <div class="emp-trend-card">
        <h3 class="emp-chart-title">Your 30-Day Attendance</h3>
        <apexchart
          v-if="trendOptions"
          type="bar"
          height="220"
          :options="trendOptions"
          :series="trendSeries"
        />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import { getEmployeePersonalStats } from '@/services/api.js'

export default {
  name: 'EmployeeDashboardTab',
  components: { apexchart: VueApexCharts },
  setup() {
    const loading = ref(true)
    const data = ref(null)
    const trendSeries = ref([])
    const trendOptions = ref(null)

    const todayStatusClass = computed(() => {
      const s = data.value?.today_status
      if (s === 'completed') return 'status-complete'
      if (s === 'checked_in') return 'status-in'
      return 'status-none'
    })
    const todayStatusIcon = computed(() => {
      const s = data.value?.today_status
      if (s === 'completed') return 'mdi-check-circle'
      if (s === 'checked_in') return 'mdi-login'
      return 'mdi-close-circle'
    })
    const todayStatusText = computed(() => {
      const s = data.value?.today_status
      if (s === 'completed') return 'Completed'
      if (s === 'checked_in') return 'Checked In'
      return 'Not Checked In'
    })

    const buildTrendChart = (trend) => {
      if (!trend || !trend.length) return

      const colorMap = {
        normal: '#10b981',
        late: '#f59e0b',
        half_day: '#f97316',
        absent: '#ef4444',
        recovered: '#6366f1',
        incomplete: '#94a3b8'
      }

      trendSeries.value = [{
        name: 'Status',
        data: trend.map(d => {
          return {
            x: new Date(d.date).getDate() + '/' + (new Date(d.date).getMonth() + 1),
            y: d.status === 'absent' ? 0 : 1,
            fillColor: colorMap[d.status] || '#94a3b8'
          }
        })
      }]

      trendOptions.value = {
        chart: {
          type: 'bar',
          toolbar: { show: false },
          fontFamily: 'Inter, sans-serif'
        },
        plotOptions: {
          bar: {
            borderRadius: 4,
            columnWidth: '60%',
            distributed: true
          }
        },
        colors: trend.map(d => colorMap[d.status] || '#94a3b8'),
        xaxis: {
          labels: { style: { colors: '#94a3b8', fontSize: '11px' }, rotate: -45 }
        },
        yaxis: {
          labels: { show: false },
          max: 1.2
        },
        legend: { show: false },
        grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
        tooltip: {
          custom: ({ dataPointIndex }) => {
            const d = trend[dataPointIndex]
            const date = new Date(d.date).toLocaleDateString('vi-VN')
            return `<div style="padding:8px 12px;font-size:13px">
              <b>${date}</b><br/>
              Status: <span style="color:${colorMap[d.status]};font-weight:600">${d.status.replace('_',' ')}</span>
            </div>`
          }
        },
        dataLabels: { enabled: false }
      }
    }

    onMounted(async () => {
      try {
        const res = await getEmployeePersonalStats()
        if (res.data?.success) {
          data.value = res.data.data
          buildTrendChart(res.data.data.trend)
        }
      } catch (e) {
        console.error('Failed to load employee stats:', e)
      } finally {
        loading.value = false
      }
    })

    return { loading, data, todayStatusClass, todayStatusIcon, todayStatusText, trendSeries, trendOptions }
  }
}
</script>

<style scoped>
.emp-dashboard { padding: 28px 32px; }
.loading-overlay {
  display: flex; align-items: center; justify-content: center; min-height: 300px;
}

.welcome-section {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 28px;
}
.welcome-text h2 {
  font-size: 22px; font-weight: 800; color: #1e293b; margin: 0;
}
.welcome-text p {
  font-size: 14px; color: #94a3b8; margin: 4px 0 0;
}
.today-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-radius: 12px;
  font-size: 13px; font-weight: 600; color: white;
}
.status-complete { background: linear-gradient(135deg, #10b981, #059669); }
.status-in { background: linear-gradient(135deg, #6366f1, #4f46e5); }
.status-none { background: linear-gradient(135deg, #94a3b8, #64748b); }

.emp-stat-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 24px;
}
.emp-stat-card {
  display: flex; align-items: center; gap: 14px;
  padding: 20px; background: white; border-radius: 16px;
  box-shadow: 0 1px 10px rgba(0,0,0,0.06); border: 1px solid #f1f5f9;
  transition: transform 0.2s;
}
.emp-stat-card:hover { transform: translateY(-2px); }
.emp-stat-icon {
  width: 48px; height: 48px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.emp-stat-info { display: flex; flex-direction: column; flex: 1; }
.emp-stat-value { font-size: 24px; font-weight: 800; color: #1e293b; }
.emp-stat-label { font-size: 12px; color: #94a3b8; font-weight: 500; }
.emp-stat-sub { font-size: 16px; color: #cbd5e1; font-weight: 600; }

.emp-trend-card {
  background: white; border-radius: 16px; padding: 24px;
  box-shadow: 0 1px 10px rgba(0,0,0,0.06); border: 1px solid #f1f5f9;
}
.emp-chart-title {
  font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 16px;
}

@media (max-width: 768px) {
  .emp-stat-cards { grid-template-columns: repeat(2, 1fr); }
  .welcome-section { flex-direction: column; gap: 12px; align-items: flex-start; }
}
</style>
