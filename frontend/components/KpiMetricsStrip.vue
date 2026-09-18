<template>
  <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3">
    
    <!-- Card 1: Measured Power (Data Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">Measured Power</span>
        <Activity class="w-3.5 h-3.5 text-surface-400" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span class="text-xl font-bold font-mono text-surface-900">{{ currentStats?.avg_actual_kwh ?? '--' }}</span>
        <span class="text-xs text-surface-500 font-mono">kWh</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Utility meter</span>
        <span class="font-mono text-surface-600">Peak: {{ currentStats?.max_actual_kwh ?? 289.4 }}</span>
      </div>
    </div>

    <!-- Card 2: Expected Baseline (ML Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">Expected Baseline</span>
        <Cpu class="w-3.5 h-3.5 text-brand-600" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span class="text-xl font-bold font-mono text-brand-700">{{ currentStats?.avg_expected_kwh ?? '--' }}</span>
        <span class="text-xs text-surface-500 font-mono">kWh</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Contextual model</span>
        <span class="font-mono text-brand-600">Load & weather</span>
      </div>
    </div>

    <!-- Card 3: Contextual Deviation (Analysis Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">Contextual Residual</span>
        <TrendingUp class="w-3.5 h-3.5 text-surface-400" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span
          :class="[
            'text-xl font-bold font-mono',
            (currentStats?.avg_residual_kwh ?? 0) > 1.0 ? 'text-amber-700' : 'text-emerald-700'
          ]"
        >
          {{ (currentStats?.avg_residual_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.avg_residual_kwh ?? '--' }}
        </span>
        <span class="text-xs text-surface-500 font-mono">kWh</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Actual − Expected</span>
        <span class="font-mono text-amber-700 font-medium">Max: +{{ currentStats?.max_residual_kwh ?? '--' }}</span>
      </div>
    </div>

    <!-- Card 4: Health & Anomaly Rate -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">Abnormal Periods</span>
        <AlertTriangle class="w-3.5 h-3.5 text-amber-500" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span class="text-xl font-bold font-mono text-amber-700">{{ currentStats?.anomaly_count ?? 0 }}</span>
        <span class="text-xs text-surface-500 font-mono">intervals</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Deviation rate</span>
        <span class="font-mono text-surface-700 font-semibold">{{ currentStats?.anomaly_rate_pct ?? '--' }}%</span>
      </div>
    </div>

    <!-- Card 5: 30-Day Efficiency Drift (Historical Comparison) -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">30-Day Drift</span>
        <Compass class="w-3.5 h-3.5 text-surface-400" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span
          :class="[
            'text-xl font-bold font-mono',
            Math.abs(currentStats?.recent_drift_kwh ?? 0) > 2.0 ? 'text-amber-700' : 'text-emerald-700'
          ]"
        >
          {{ (currentStats?.recent_drift_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.recent_drift_kwh ?? '0.00' }}
        </span>
        <span class="text-xs text-surface-500 font-mono">kWh</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Vs 7-day median</span>
        <span class="text-[10px] px-1.5 py-0.2 rounded font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/60">
          Gradual shift
        </span>
      </div>
    </div>

    <!-- Card 6: Operating COP & Waste Impact -->
    <div class="bg-white border border-surface-200 rounded-xl p-3.5 shadow-card hover:border-surface-300 transition-colors">
      <div class="flex items-center justify-between text-surface-500 text-xs mb-1">
        <span class="font-medium">Estimated COP</span>
        <Gauge class="w-3.5 h-3.5 text-emerald-600" />
      </div>
      <div class="flex items-baseline space-x-1">
        <span class="text-xl font-bold font-mono text-emerald-700">{{ currentStats?.avg_cop_approx ?? '--' }}</span>
        <span class="text-xs text-surface-500 font-mono">COP</span>
      </div>
      <div class="mt-1 flex items-center justify-between text-[11px] text-surface-500">
        <span>Thermal coefficient</span>
        <span class="font-mono text-surface-700 font-medium">{{ currentStats?.event_count ?? '--' }} episodes</span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Activity, Cpu, TrendingUp, AlertTriangle, Compass, Gauge } from 'lucide-vue-next'

defineProps<{
  currentStats?: {
    avg_actual_kwh: number
    avg_expected_kwh: number
    avg_residual_kwh: number
    max_residual_kwh: number
    max_actual_kwh?: number
    anomaly_count: number
    anomaly_rate_pct: number
    event_count: number
    avg_cop_approx: number
    recent_drift_kwh: number
    total_records: number
  }
}>()
</script>
