<template>
  <div class="dashboard-container">
    <!-- Loading State -->
    <div v-if="loading" class="loading-overlay">
      <v-progress-circular indeterminate color="primary" size="48" />
      <span class="loading-text">Loading Dashboard...</span>
    </div>

    <div v-else>
      <!-- Stat Cards Row -->
      <div class="stat-cards-row">
        <div class="stat-card present">
          <div class="stat-icon-wrap">
            <v-icon size="28" color="white">mdi-account-check</v-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.today?.present || 0 }}</span>
            <span class="stat-label">Present Today</span>
          </div>
          <div class="stat-total">/ {{ stats.today?.total_employees || 0 }}</div>
        </div>

        <div class="stat-card late">
          <div class="stat-icon-wrap">
            <v-icon size="28" color="white">mdi-clock-alert</v-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.today?.late || 0 }}</span>
            <span class="stat-label">Late Today</span>
          </div>
        </div>

        <div class="stat-card absent">
          <div class="stat-icon-wrap">
            <v-icon size="28" color="white">mdi-account-off</v-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.today?.absent || 0 }}</span>
            <span class="stat-label">Absent Today</span>
          </div>
        </div>

        <div class="stat-card trained">
          <div class="stat-icon-wrap">
            <v-icon size="28" color="white">mdi-face-recognition</v-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.system?.face_trained || 0 }}</span>
            <span class="stat-label">Face Trained</span>
          </div>
          <div class="stat-total">/ {{ (stats.system?.face_trained || 0) + (stats.system?.face_not_trained || 0) }}</div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <!-- Attendance Trend Chart -->
        <div class="chart-card trend-chart">
          <div class="chart-header">
            <h3 class="chart-title">Attendance Trend</h3>
            <div class="chart-actions">
              <button
                :class="['period-btn', { active: trendPeriod === 'week' }]"
                @click="loadTrend('week')"
              >7 Days</button>
              <button
                :class="['period-btn', { active: trendPeriod === 'month' }]"
                @click="loadTrend('month')"
              >30 Days</button>
            </div>
          </div>
          <apexchart
            v-if="trendOptions"
            type="area"
            height="300"
            :options="trendOptions"
            :series="trendSeries"
          />
        </div>

        <!-- Attendance Distribution Pie -->
        <div class="chart-card pie-chart">
          <div class="chart-header">
            <h3 class="chart-title">Today's Distribution</h3>
          </div>
          <apexchart
            v-if="pieOptions"
            type="donut"
            height="300"
            :options="pieOptions"
            :series="pieSeries"
          />
        </div>
      </div>

      <!-- Department Summary & Heatmap -->
      <div class="charts-row">
        <!-- Department Summary -->
        <div class="chart-card dept-chart">
          <div class="chart-header">
            <h3 class="chart-title">Department Overview</h3>
          </div>
          <apexchart
            v-if="deptOptions && deptSeries.length"
            type="bar"
            height="300"
            :options="deptOptions"
            :series="deptSeries"
          />
          <div v-else class="no-data">
            <v-icon size="48" color="grey-lighten-1">mdi-office-building-outline</v-icon>
            <p>No department data available</p>
          </div>
        </div>

        <!-- Heatmap -->
        <div class="chart-card heatmap-chart">
          <div class="chart-header">
            <h3 class="chart-title">Check-in Heatmap</h3>
            <span class="chart-subtitle">Frequency by hour</span>
          </div>
          <apexchart
            v-if="heatmapOptions && heatmapSeries.length"
            type="heatmap"
            height="300"
            :options="heatmapOptions"
            :series="heatmapSeries"
          />
          <div v-else class="no-data">
            <v-icon size="48" color="grey-lighten-1">mdi-chart-box-outline</v-icon>
            <p>No heatmap data available</p>
          </div>
        </div>
      </div>

      <!-- Month Summary -->
      <div class="month-summary-row">
        <div class="month-summary-card">
          <v-icon size="24" color="#6366f1">mdi-calendar-month</v-icon>
          <div>
            <span class="month-val">{{ stats.month?.total_attendance_days || 0 }}</span>
            <span class="month-lbl">Total Attendance Days (This Month)</span>
          </div>
        </div>
        <div class="month-summary-card">
          <v-icon size="24" color="#f59e0b">mdi-clock-fast</v-icon>
          <div>
            <span class="month-val">{{ stats.month?.total_late || 0 }}</span>
            <span class="month-lbl">Late Arrivals (This Month)</span>
          </div>
        </div>
        <div class="month-summary-card">
          <v-icon size="24" color="#10b981">mdi-timer-outline</v-icon>
          <div>
            <span class="month-val">{{ stats.system?.work_start || '08:30' }} - {{ stats.system?.work_end || '17:30' }}</span>
            <span class="month-lbl">Working Hours</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import VueApexCharts from 'vue3-apexcharts'
import {
  getAdminDashboardStats,
  getAttendanceTrend,
  getDepartmentSummary,
  getAttendanceHeatmap
} from '@/services/api.js'

export default {
  name: 'DashboardTab',
  components: {
    apexchart: VueApexCharts
  },
  setup() {
    const loading = ref(true)
    const stats = ref({})
    const trendPeriod = ref('week')

    // Trend chart
    const trendSeries = ref([])
    const trendOptions = ref(null)

    // Pie chart
    const pieSeries = ref([])
    const pieOptions = ref(null)

    // Department chart
    const deptSeries = ref([])
    const deptOptions = ref(null)

    // Heatmap
    const heatmapSeries = ref([])
    const heatmapOptions = ref(null)

    const loadStats = async () => {
      try {
        const res = await getAdminDashboardStats()
        if (res.data?.success) {
          stats.value = res.data.data
          updatePieChart()
        }
      } catch (e) {
        console.error('Failed to load stats:', e)
      }
    }

    const loadTrend = async (period = 'week') => {
      trendPeriod.value = period
      try {
        const res = await getAttendanceTrend(period)
        if (res.data?.success) {
          const data = res.data.data.data.filter(d => !d.is_weekend)
          
          trendSeries.value = [
            { name: 'Normal', data: data.map(d => d.normal) },
            { name: 'Late', data: data.map(d => d.late) },
            { name: 'Absent', data: data.map(d => d.absent) }
          ]

          trendOptions.value = {
            chart: {
              type: 'area',
              toolbar: { show: false },
              fontFamily: 'Inter, sans-serif',
              animations: { enabled: true, speed: 600 }
            },
            colors: ['#10b981', '#f59e0b', '#ef4444'],
            stroke: { curve: 'smooth', width: 2.5 },
            fill: {
              type: 'gradient',
              gradient: { opacityFrom: 0.4, opacityTo: 0.05 }
            },
            xaxis: {
              categories: data.map(d => {
                const date = new Date(d.date)
                return `${date.getDate()}/${date.getMonth() + 1}`
              }),
              labels: { style: { colors: '#94a3b8', fontSize: '12px' } }
            },
            yaxis: {
              labels: { style: { colors: '#94a3b8', fontSize: '12px' } }
            },
            legend: {
              position: 'top',
              horizontalAlign: 'right',
              fontSize: '13px',
              markers: { radius: 4 }
            },
            grid: {
              borderColor: '#f1f5f9',
              strokeDashArray: 4
            },
            tooltip: { theme: 'dark' },
            dataLabels: { enabled: false }
          }
        }
      } catch (e) {
        console.error('Failed to load trend:', e)
      }
    }

    const updatePieChart = () => {
      const today = stats.value.today || {}
      const normal = Math.max(0, (today.present || 0) - (today.late || 0))
      
      pieSeries.value = [normal, today.late || 0, today.absent || 0]
      
      pieOptions.value = {
        chart: {
          type: 'donut',
          fontFamily: 'Inter, sans-serif',
          animations: { enabled: true, speed: 600 }
        },
        labels: ['Normal', 'Late', 'Absent'],
        colors: ['#10b981', '#f59e0b', '#ef4444'],
        legend: {
          position: 'bottom',
          fontSize: '13px',
          markers: { radius: 4 }
        },
        plotOptions: {
          pie: {
            donut: {
              size: '68%',
              labels: {
                show: true,
                total: {
                  show: true,
                  label: 'Total',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#1e293b'
                }
              }
            }
          }
        },
        dataLabels: {
          enabled: true,
          style: { fontSize: '13px' }
        },
        stroke: { width: 2, colors: ['#fff'] },
        tooltip: { theme: 'dark' }
      }
    }

    const loadDepartments = async () => {
      try {
        const res = await getDepartmentSummary()
        if (res.data?.success && res.data.data.length) {
          const data = res.data.data

          deptSeries.value = [
            { name: 'Present', data: data.map(d => d.present) },
            { name: 'Late', data: data.map(d => d.late) },
            { name: 'Absent', data: data.map(d => d.absent) }
          ]

          deptOptions.value = {
            chart: {
              type: 'bar',
              stacked: true,
              toolbar: { show: false },
              fontFamily: 'Inter, sans-serif'
            },
            colors: ['#10b981', '#f59e0b', '#ef4444'],
            xaxis: {
              categories: data.map(d => d.department),
              labels: { style: { colors: '#94a3b8', fontSize: '12px' } }
            },
            yaxis: {
              labels: { style: { colors: '#94a3b8', fontSize: '12px' } }
            },
            legend: {
              position: 'top',
              horizontalAlign: 'right',
              fontSize: '13px'
            },
            plotOptions: {
              bar: {
                borderRadius: 6,
                columnWidth: '50%'
              }
            },
            grid: { borderColor: '#f1f5f9', strokeDashArray: 4 },
            tooltip: { theme: 'dark' },
            dataLabels: { enabled: false }
          }
        }
      } catch (e) {
        console.error('Failed to load departments:', e)
      }
    }

    const loadHeatmap = async () => {
      try {
        const res = await getAttendanceHeatmap()
        if (res.data?.success && res.data.data.series) {
          heatmapSeries.value = res.data.data.series

          heatmapOptions.value = {
            chart: {
              type: 'heatmap',
              toolbar: { show: false },
              fontFamily: 'Inter, sans-serif'
            },
            colors: ['#6366f1'],
            plotOptions: {
              heatmap: {
                radius: 4,
                colorScale: {
                  ranges: [
                    { from: 0, to: 0, color: '#f1f5f9', name: 'None' },
                    { from: 1, to: 3, color: '#c7d2fe', name: 'Low' },
                    { from: 4, to: 8, color: '#818cf8', name: 'Medium' },
                    { from: 9, to: 100, color: '#4f46e5', name: 'High' }
                  ]
                }
              }
            },
            dataLabels: { enabled: false },
            xaxis: {
              labels: {
                style: { colors: '#94a3b8', fontSize: '11px' },
                rotate: -45
              }
            },
            yaxis: {
              labels: { style: { colors: '#94a3b8', fontSize: '11px' } }
            },
            tooltip: { theme: 'dark' }
          }
        }
      } catch (e) {
        console.error('Failed to load heatmap:', e)
      }
    }

    onMounted(async () => {
      loading.value = true
      await Promise.all([
        loadStats(),
        loadTrend('week'),
        loadDepartments(),
        loadHeatmap()
      ])
      loading.value = false
    })

    return {
      loading,
      stats,
      trendPeriod,
      trendSeries,
      trendOptions,
      pieSeries,
      pieOptions,
      deptSeries,
      deptOptions,
      heatmapSeries,
      heatmapOptions,
      loadTrend
    }
  }
}
</script>

<style scoped>
.dashboard-container {
  padding: 28px 32px;
  min-height: 100%;
}

/* Loading */
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  min-height: 400px;
}
.loading-text {
  color: #94a3b8;
  font-size: 15px;
  font-weight: 500;
}

/* Stat Cards */
.stat-cards-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 28px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 22px 24px;
  border-radius: 16px;
  background: white;
  box-shadow: 0 1px 10px rgba(0,0,0,0.06);
  border: 1px solid #f1f5f9;
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0,0,0,0.1);
}
.stat-icon-wrap {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-card.present .stat-icon-wrap { background: linear-gradient(135deg, #10b981, #059669); }
.stat-card.late .stat-icon-wrap { background: linear-gradient(135deg, #f59e0b, #d97706); }
.stat-card.absent .stat-icon-wrap { background: linear-gradient(135deg, #ef4444, #dc2626); }
.stat-card.trained .stat-icon-wrap { background: linear-gradient(135deg, #6366f1, #4f46e5); }

.stat-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.stat-value {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
}
.stat-label {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 500;
  margin-top: 4px;
}
.stat-total {
  font-size: 18px;
  font-weight: 600;
  color: #cbd5e1;
}

/* Charts Row */
.charts-row {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 20px;
  margin-bottom: 24px;
}
.chart-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 1px 10px rgba(0,0,0,0.06);
  border: 1px solid #f1f5f9;
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}
.chart-subtitle {
  font-size: 13px;
  color: #94a3b8;
}
.chart-actions {
  display: flex;
  gap: 6px;
}
.period-btn {
  padding: 6px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}
.period-btn:hover {
  background: #f8fafc;
  border-color: #cbd5e1;
}
.period-btn.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

/* No Data */
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 12px;
}
.no-data p {
  color: #94a3b8;
  font-size: 14px;
  margin: 0;
}

/* Month Summary */
.month-summary-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.month-summary-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 1px 10px rgba(0,0,0,0.06);
  border: 1px solid #f1f5f9;
}
.month-val {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}
.month-lbl {
  display: block;
  font-size: 12px;
  color: #94a3b8;
  font-weight: 500;
}

/* Responsive */
@media (max-width: 1024px) {
  .stat-cards-row { grid-template-columns: repeat(2, 1fr); }
  .charts-row { grid-template-columns: 1fr; }
  .month-summary-row { grid-template-columns: 1fr; }
}
@media (max-width: 640px) {
  .dashboard-container { padding: 16px; }
  .stat-cards-row { grid-template-columns: 1fr; }
}
</style>
