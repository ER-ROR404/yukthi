<template>
  <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4">
    
    <!-- Card 1: Measured Power (Data Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-surface-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">Measured Power</span>
        <div class="w-7 h-7 rounded-md bg-red-50 border border-red-200/80 flex items-center justify-center">
          <Activity class="w-3.5 h-3.5 text-red-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-surface-900 tracking-tight">{{ currentStats?.avg_actual_kwh ?? '--' }}</span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">kWh</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Power meter</span>
        <span class="font-mono text-surface-700 font-semibold">Peak: {{ currentStats?.max_actual_kwh ?? 289.4 }}</span>
      </div>
    </div>

    <!-- Card 2: Expected Baseline (ML Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-surface-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">Expected Baseline</span>
        <div class="w-7 h-7 rounded-md bg-brand-50 border border-brand-200/80 flex items-center justify-center">
          <Cpu class="w-3.5 h-3.5 text-brand-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-brand-700 tracking-tight">{{ currentStats?.avg_expected_kwh ?? '--' }}</span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">kWh</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Contextual model</span>
        <span class="font-mono text-brand-700 font-semibold">Load & weather</span>
      </div>
    </div>

    <!-- Card 3: Contextual Deviation (Analysis Level) -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-surface-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">Contextual Residual</span>
        <div class="w-7 h-7 rounded-md bg-amber-50 border border-amber-200/80 flex items-center justify-center">
          <TrendingUp class="w-3.5 h-3.5 text-amber-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span
          :class="[
            'text-2xl sm:text-3xl font-bold font-mono tracking-tight',
            (currentStats?.avg_residual_kwh ?? 0) > 1.0 ? 'text-amber-700' : 'text-emerald-700'
          ]"
        >
          {{ (currentStats?.avg_residual_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.avg_residual_kwh ?? '--' }}
        </span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">kWh</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Actual − Expected</span>
        <span class="font-mono text-amber-700 font-semibold">Max: +{{ currentStats?.max_residual_kwh ?? '--' }}</span>
      </div>
    </div>

    <!-- Card 4: Health & Anomaly Rate -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-surface-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">Abnormal Intervals</span>
        <div class="w-7 h-7 rounded-md bg-amber-50 border border-amber-200/80 flex items-center justify-center">
          <AlertTriangle class="w-3.5 h-3.5 text-amber-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-amber-700 tracking-tight">{{ currentStats?.anomaly_count ?? 0 }}</span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">periods</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Deviation rate</span>
        <span class="font-mono text-surface-800 font-semibold">{{ currentStats?.anomaly_rate_pct ?? '--' }}%</span>
      </div>
    </div>

    <!-- Card 5: Persistent Episodes (Clustered Maintenance Events) -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-orange-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">Persistent Episodes</span>
        <div class="w-7 h-7 rounded-md bg-orange-50 border border-orange-200/80 flex items-center justify-center">
          <Layers class="w-3.5 h-3.5 text-orange-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-orange-700 tracking-tight">{{ currentStats?.event_count ?? '--' }}</span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">episodes</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Consolidated</span>
        <span class="font-mono text-surface-700 font-semibold">Maintenance events</span>
      </div>
    </div>

    <!-- Card 6: 30-Day Efficiency Drift (Historical Comparison) -->
    <div class="bg-white border border-surface-200 rounded-xl p-4 sm:p-5 shadow-card hover:border-surface-300 hover:shadow-hover transition-all">
      <div class="flex items-center justify-between text-surface-600 text-xs sm:text-sm font-semibold mb-2">
        <span class="font-sans">30-Day Drift</span>
        <div class="w-7 h-7 rounded-md bg-emerald-50 border border-emerald-200/80 flex items-center justify-center">
          <Compass class="w-3.5 h-3.5 text-emerald-600" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1">
        <span
          :class="[
            'text-2xl sm:text-3xl font-bold font-mono tracking-tight',
            Math.abs(currentStats?.recent_drift_kwh ?? 0) > 2.0 ? 'text-amber-700' : 'text-emerald-700'
          ]"
        >
          {{ (currentStats?.recent_drift_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.recent_drift_kwh ?? '0.00' }}
        </span>
        <span class="text-xs sm:text-sm text-surface-500 font-mono font-medium">kWh</span>
      </div>
      <div class="mt-2 pt-2 border-t border-surface-100 flex items-center justify-between text-xs text-surface-500 font-sans">
        <span>Vs 7-day median</span>
        <span class="text-xs px-2 py-0.5 rounded font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
          Normal Drift
        </span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Activity, Cpu, TrendingUp, AlertTriangle, Compass, Layers } from 'lucide-vue-next'

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
    avg_cop_approx?: number
    recent_drift_kwh: number
    total_records: number
  }
}>()
</script>
