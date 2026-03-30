<template>
  <div class="payroll-container">
    <!-- Header Controls -->
    <div class="payroll-header">
      <div class="header-left">
        <h3 class="payroll-title">
          <v-icon size="24" class="mr-2">mdi-cash-multiple</v-icon>
          Payroll Management
        </h3>
      </div>
      <div class="header-controls">
        <v-select
          v-model="selectedMonth"
          :items="months"
          item-title="label"
          item-value="value"
          label="Month"
          variant="outlined"
          density="compact"
          hide-details
          class="month-select"
        />
        <v-select
          v-model="selectedYear"
          :items="years"
          label="Year"
          variant="outlined"
          density="compact"
          hide-details
          class="year-select"
        />
        <v-btn color="primary" variant="flat" @click="loadPayroll" :loading="loading" prepend-icon="mdi-magnify">
          View
        </v-btn>
        <v-btn color="success" variant="flat" @click="handleGenerate" :loading="generating" prepend-icon="mdi-calculator">
          Generate
        </v-btn>
        <v-btn color="info" variant="flat" @click="handleExport" :loading="exporting" prepend-icon="mdi-file-excel">
          Export
        </v-btn>
        <v-btn variant="outlined" @click="showConfigDialog = true" prepend-icon="mdi-cog">
          Config
        </v-btn>
      </div>
    </div>

    <!-- Summary Cards -->
    <div v-if="payrollData" class="summary-cards">
      <div class="summary-card">
        <v-icon size="24" color="#10b981">mdi-account-group</v-icon>
        <div>
          <span class="summary-value">{{ payrollData.total_employees }}</span>
          <span class="summary-label">Employees</span>
        </div>
      </div>
      <div class="summary-card">
        <v-icon size="24" color="#6366f1">mdi-cash</v-icon>
        <div>
          <span class="summary-value">{{ formatCurrency(payrollData.summary?.total_gross) }}</span>
          <span class="summary-label">Gross Total</span>
        </div>
      </div>
      <div class="summary-card">
        <v-icon size="24" color="#ef4444">mdi-cash-minus</v-icon>
        <div>
          <span class="summary-value">{{ formatCurrency(payrollData.summary?.total_deductions) }}</span>
          <span class="summary-label">Total Deductions</span>
        </div>
      </div>
      <div class="summary-card highlight">
        <v-icon size="24" color="white">mdi-cash-check</v-icon>
        <div>
          <span class="summary-value" style="color: white">{{ formatCurrency(payrollData.summary?.total_net) }}</span>
          <span class="summary-label" style="color: rgba(255,255,255,0.8)">Net Total</span>
        </div>
      </div>
    </div>

    <!-- Payroll Table -->
    <div class="payroll-table-wrap">
      <v-data-table
        :headers="tableHeaders"
        :items="payrollData?.records || []"
        :loading="loading"
        class="payroll-table"
        :items-per-page="20"
        :sort-by="[{ key: 'employee_id', order: 'asc' }]"
      >
        <template v-slot:no-data>
          <div class="no-data-msg">
            <v-icon size="56" color="grey-lighten-1">mdi-cash-register</v-icon>
            <p>No payroll data for {{ selectedMonth }}/{{ selectedYear }}</p>
            <p class="no-data-hint">Click "Generate" to create payroll records</p>
          </div>
        </template>

        <template v-slot:item.full_name="{ item }">
          <div>
            <strong>{{ item.full_name || item.employee_id }}</strong>
            <div class="dept-text">{{ item.department || '' }}</div>
          </div>
        </template>
        <template v-slot:item.base_salary="{ item }">
          {{ formatCurrency(item.base_salary) }}
        </template>
        <template v-slot:item.work_salary="{ item }">
          {{ formatCurrency(item.work_salary) }}
        </template>
        <template v-slot:item.ot_pay="{ item }">
          <span v-if="item.ot_pay > 0" class="text-green">+{{ formatCurrency(item.ot_pay) }}</span>
          <span v-else class="text-disabled">-</span>
        </template>
        <template v-slot:item.total_deductions="{ item }">
          <span v-if="item.total_deductions > 0" class="text-red">-{{ formatCurrency(item.total_deductions) }}</span>
          <span v-else class="text-disabled">0</span>
        </template>
        <template v-slot:item.net_salary="{ item }">
          <strong class="net-salary">{{ formatCurrency(item.net_salary) }}</strong>
        </template>
        <template v-slot:item.late_count="{ item }">
          <v-chip v-if="item.late_count > 0" color="orange" size="x-small" variant="tonal">{{ item.late_count }}</v-chip>
          <span v-else class="text-disabled">0</span>
        </template>
        <template v-slot:item.absent_days="{ item }">
          <v-chip v-if="item.absent_days > 0" color="red" size="x-small" variant="tonal">{{ item.absent_days }}</v-chip>
          <span v-else class="text-disabled">0</span>
        </template>
        <template v-slot:item.ot_hours="{ item }">
          <v-chip v-if="item.ot_hours > 0" color="green" size="x-small" variant="tonal">{{ item.ot_hours }}h</v-chip>
          <span v-else class="text-disabled">0</span>
        </template>
      </v-data-table>
    </div>

    <!-- Config Dialog -->
    <v-dialog v-model="showConfigDialog" max-width="520" persistent>
      <v-card class="config-card">
        <v-card-title class="config-title">
          <v-icon class="mr-2">mdi-cog</v-icon>
          Payroll Configuration
        </v-card-title>
        <v-card-text>
          <v-text-field v-model.number="configForm.base_salary" label="Base Salary (VNĐ)" variant="outlined" density="comfortable" type="number" class="mb-3" />
          <v-text-field v-model.number="configForm.ot_multiplier" label="OT Multiplier" variant="outlined" density="comfortable" type="number" step="0.1" class="mb-3" />
          <v-text-field v-model.number="configForm.late_deduction" label="Late Deduction (VNĐ/time)" variant="outlined" density="comfortable" type="number" class="mb-3" />
          <v-text-field v-model.number="configForm.absent_deduction_rate" label="Absent Deduction Rate" variant="outlined" density="comfortable" type="number" step="0.1" class="mb-3" />
          <v-text-field v-model.number="configForm.working_days_per_month" label="Working Days/Month" variant="outlined" density="comfortable" type="number" />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showConfigDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="saveConfig" :loading="savingConfig">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000" location="top">
      {{ snackbar.text }}
    </v-snackbar>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import {
  getPayrollList,
  generatePayroll,
  exportPayroll,
  getPayrollConfig,
  updatePayrollConfig
} from '@/services/api.js'

export default {
  name: 'PayrollTab',
  setup() {
    const now = new Date()
    const selectedMonth = ref(now.getMonth() + 1)
    const selectedYear = ref(now.getFullYear())
    const loading = ref(false)
    const generating = ref(false)
    const exporting = ref(false)
    const savingConfig = ref(false)
    const showConfigDialog = ref(false)
    const payrollData = ref(null)
    const snackbar = reactive({ show: false, text: '', color: 'success' })

    const configForm = reactive({
      base_salary: 10000000,
      ot_multiplier: 1.5,
      late_deduction: 50000,
      absent_deduction_rate: 1.0,
      working_days_per_month: 22
    })

    const months = Array.from({ length: 12 }, (_, i) => ({
      value: i + 1,
      label: `Tháng ${i + 1}`
    }))
    const years = Array.from({ length: 5 }, (_, i) => now.getFullYear() - 2 + i)

    const tableHeaders = [
      { title: 'Employee ID', key: 'employee_id', width: '90px' },
      { title: 'Full Name', key: 'full_name', width: '180px' },
      { title: 'Work Days', key: 'actual_work_days', width: '80px', align: 'center' },
      { title: 'Late', key: 'late_count', width: '60px', align: 'center' },
      { title: 'Absent', key: 'absent_days', width: '60px', align: 'center' },
      { title: 'OT Hours', key: 'ot_hours', width: '70px', align: 'center' },
      { title: 'Base Salary', key: 'base_salary', width: '120px', align: 'end' },
      { title: 'Work Salary', key: 'work_salary', width: '120px', align: 'end' },
      { title: 'OT Pay', key: 'ot_pay', width: '100px', align: 'end' },
      { title: 'Deductions', key: 'total_deductions', width: '110px', align: 'end' },
      { title: 'Net Salary', key: 'net_salary', width: '130px', align: 'end' }
    ]

    const formatCurrency = (val) => {
      if (!val && val !== 0) return '0'
      return new Intl.NumberFormat('vi-VN').format(Math.round(val)) + 'đ'
    }

    const notify = (text, color = 'success') => {
      snackbar.text = text
      snackbar.color = color
      snackbar.show = true
    }

    const loadPayroll = async () => {
      loading.value = true
      try {
        const res = await getPayrollList(selectedMonth.value, selectedYear.value)
        if (res.data?.success) {
          payrollData.value = res.data.data
        }
      } catch (e) {
        console.error(e)
        notify('Failed to load payroll', 'error')
      } finally {
        loading.value = false
      }
    }

    const handleGenerate = async () => {
      generating.value = true
      try {
        const res = await generatePayroll(selectedMonth.value, selectedYear.value)
        if (res.data?.success) {
          notify(`Payroll generated for ${res.data.data.processed} employees`)
          await loadPayroll()
        }
      } catch (e) {
        notify('Failed to generate payroll', 'error')
      } finally {
        generating.value = false
      }
    }

    const handleExport = async () => {
      exporting.value = true
      try {
        const res = await exportPayroll(selectedMonth.value, selectedYear.value)
        if (res.data?.success) {
          const url = res.data.data.download_url
          window.open(url, '_blank')
          notify('Excel exported successfully')
        }
      } catch (e) {
        notify('Failed to export payroll', 'error')
      } finally {
        exporting.value = false
      }
    }

    const loadConfig = async () => {
      try {
        const res = await getPayrollConfig()
        if (res.data?.success) {
          Object.assign(configForm, res.data.data)
        }
      } catch (e) {
        console.error('Failed to load config:', e)
      }
    }

    const saveConfig = async () => {
      savingConfig.value = true
      try {
        const res = await updatePayrollConfig({ ...configForm })
        if (res.data?.success) {
          notify('Configuration saved')
          showConfigDialog.value = false
        }
      } catch (e) {
        notify('Failed to save config', 'error')
      } finally {
        savingConfig.value = false
      }
    }

    onMounted(() => {
      loadPayroll()
      loadConfig()
    })

    return {
      selectedMonth, selectedYear, loading, generating, exporting, savingConfig,
      showConfigDialog, payrollData, snackbar, configForm, months, years,
      tableHeaders, formatCurrency, loadPayroll, handleGenerate, handleExport,
      loadConfig, saveConfig, notify
    }
  }
}
</script>

<style scoped>
.payroll-container { padding: 28px 32px; }

.payroll-header {
  display: flex; align-items: center; justify-content: space-between;
  flex-wrap: wrap; gap: 16px; margin-bottom: 24px;
}
.payroll-title {
  font-size: 18px; font-weight: 700; color: #1e293b; margin: 0;
  display: flex; align-items: center;
}
.header-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.month-select { max-width: 140px; }
.year-select { max-width: 100px; }

.summary-cards {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;
}
.summary-card {
  display: flex; align-items: center; gap: 14px;
  padding: 18px 20px; background: white; border-radius: 14px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06); border: 1px solid #f1f5f9;
}
.summary-card.highlight {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.summary-value { display: block; font-size: 18px; font-weight: 800; color: #1e293b; }
.summary-label { display: block; font-size: 12px; color: #94a3b8; font-weight: 500; }

.payroll-table-wrap {
  background: white; border-radius: 14px;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06); border: 1px solid #f1f5f9;
  overflow: hidden;
}

.no-data-msg { text-align: center; padding: 48px 0; }
.no-data-msg p { color: #94a3b8; margin: 8px 0; }
.no-data-hint { font-size: 13px; }

.dept-text { font-size: 12px; color: #94a3b8; }
.text-green { color: #10b981; font-weight: 600; }
.text-red { color: #ef4444; font-weight: 600; }
.text-disabled { color: #cbd5e1; }
.net-salary { color: #4f46e5; font-size: 14px; }

.config-card { border-radius: 16px !important; }
.config-title { font-size: 16px; font-weight: 700; padding: 20px 24px 12px; }

@media (max-width: 1024px) {
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .header-controls { width: 100%; }
}
@media (max-width: 640px) {
  .payroll-container { padding: 16px; }
  .summary-cards { grid-template-columns: 1fr; }
}
</style>
