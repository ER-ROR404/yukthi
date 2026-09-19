<template>
  <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3.5 sm:gap-4">
    
    <!-- Card 1: Measured Power (Data Level) -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">Measured Power</span>
        <div class="w-8 h-8 rounded-lg bg-red-100 border border-red-300 flex items-center justify-center">
          <Activity class="w-4 h-4 text-red-700" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-slate-950 tracking-tight">{{ currentStats?.avg_actual_kwh ?? '--' }}</span>
        <span class="text-sm text-slate-600 font-mono font-semibold">kWh</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Power Meter</span>
        <span class="font-mono text-slate-900 font-bold">Peak: {{ currentStats?.max_actual_kwh ?? 289.4 }}</span>
      </div>
    </div>

    <!-- Card 2: Expected Baseline (ML Level) -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">Expected Baseline</span>
        <div class="w-8 h-8 rounded-lg bg-blue-100 border border-blue-300 flex items-center justify-center">
          <Cpu class="w-4 h-4 text-blue-700" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-blue-800 tracking-tight">{{ currentStats?.avg_expected_kwh ?? '--' }}</span>
        <span class="text-sm text-slate-600 font-mono font-semibold">kWh</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Contextual Model</span>
        <span class="font-mono text-blue-800 font-bold">Load & Weather</span>
      </div>
    </div>

    <!-- Card 3: Contextual Deviation (Analysis Level) -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">Contextual Residual</span>
        <div class="w-8 h-8 rounded-lg bg-amber-100 border border-amber-300 flex items-center justify-center">
          <TrendingUp class="w-4 h-4 text-amber-800" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span
          :class="[
            'text-2xl sm:text-3xl font-bold font-mono tracking-tight',
            (currentStats?.avg_residual_kwh ?? 0) > 1.0 ? 'text-amber-800' : 'text-emerald-800'
          ]"
        >
          {{ (currentStats?.avg_residual_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.avg_residual_kwh ?? '--' }}
        </span>
        <span class="text-sm text-slate-600 font-mono font-semibold">kWh</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Actual − Model</span>
        <span class="font-mono text-amber-900 font-bold">Max: +{{ currentStats?.max_residual_kwh ?? '--' }}</span>
      </div>
    </div>

    <!-- Card 4: Health & Anomaly Rate -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">Abnormal Intervals</span>
        <div class="w-8 h-8 rounded-lg bg-orange-100 border border-orange-300 flex items-center justify-center">
          <AlertTriangle class="w-4 h-4 text-orange-800" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-orange-800 tracking-tight">{{ currentStats?.anomaly_count ?? 0 }}</span>
        <span class="text-sm text-slate-600 font-mono font-semibold">periods</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Deviation Rate</span>
        <span class="font-mono text-slate-950 font-bold">{{ currentStats?.anomaly_rate_pct ?? '--' }}%</span>
      </div>
    </div>

    <!-- Card 5: Operational Health Index (Clustered Maintenance Indicator) -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">Health Indicator</span>
        <div class="w-8 h-8 rounded-lg bg-emerald-100 border border-emerald-300 flex items-center justify-center">
          <ShieldCheck class="w-4 h-4 text-emerald-800" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span class="text-2xl sm:text-3xl font-bold font-mono text-emerald-800 tracking-tight">
          {{ (100 - (currentStats?.anomaly_rate_pct ?? 0)).toFixed(1) }}%
        </span>
        <span class="text-sm text-slate-600 font-mono font-semibold">Nominal</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Fault Episodes</span>
        <span class="font-mono text-slate-950 font-bold">{{ currentStats?.event_count ?? '--' }} events</span>
      </div>
    </div>

    <!-- Card 6: 30-Day Efficiency Drift (Historical Comparison) -->
    <div class="card-solid bg-white border border-slate-300 rounded-xl p-4 sm:p-5 shadow-xs hover:border-slate-400 transition-all">
      <div class="flex items-center justify-between text-slate-700 text-sm font-bold mb-2">
        <span class="font-sans">30-Day Drift</span>
        <div class="w-8 h-8 rounded-lg bg-slate-200 border border-slate-300 flex items-center justify-center">
          <Compass class="w-4 h-4 text-slate-800" />
        </div>
      </div>
      <div class="flex items-baseline space-x-1.5 my-1.5">
        <span
          :class="[
            'text-2xl sm:text-3xl font-bold font-mono tracking-tight',
            Math.abs(currentStats?.recent_drift_kwh ?? 0) > 2.0 ? 'text-amber-800' : 'text-emerald-800'
          ]"
        >
          {{ (currentStats?.recent_drift_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.recent_drift_kwh ?? '0.00' }}
        </span>
        <span class="text-sm text-slate-600 font-mono font-semibold">kWh</span>
      </div>
      <div class="mt-2.5 pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs sm:text-sm text-slate-600 font-sans">
        <span class="font-medium">Vs 7d Median</span>
        <span class="text-xs px-2 py-0.5 rounded font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
          Normal Drift
        </span>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { Activity, Cpu, TrendingUp, AlertTriangle, Compass, ShieldCheck } from 'lucide-vue-next'

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
