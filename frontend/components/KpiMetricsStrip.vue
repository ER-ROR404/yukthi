<template>
  <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
    <!-- Card 1: Actual Energy -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Avg Actual Energy</span>
        <Activity class="w-3.5 h-3.5 text-status-crimson" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span class="text-xl font-bold font-mono text-cockpit-100">{{ currentStats?.avg_actual_kwh ?? '--' }}</span>
        <span class="text-xs text-cockpit-300 font-mono">kWh</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        Measured power meter
      </div>
    </div>

    <!-- Card 2: Expected Baseline -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Avg Expected</span>
        <Cpu class="w-3.5 h-3.5 text-status-blue" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span class="text-xl font-bold font-mono text-status-blue">{{ currentStats?.avg_expected_kwh ?? '--' }}</span>
        <span class="text-xs text-cockpit-300 font-mono">kWh</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        CatBoost contextual model
      </div>
    </div>

    <!-- Card 3: Net Residual Deviation -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Avg Deviation</span>
        <TrendingUp class="w-3.5 h-3.5 text-status-amber" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span
          :class="[
            'text-xl font-bold font-mono',
            (currentStats?.avg_residual_kwh ?? 0) > 0 ? 'text-status-amber' : 'text-status-emerald'
          ]"
        >
          {{ (currentStats?.avg_residual_kwh ?? 0) > 0 ? '+' : '' }}{{ currentStats?.avg_residual_kwh ?? '--' }}
        </span>
        <span class="text-xs text-cockpit-300 font-mono">kWh</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        Max: +{{ currentStats?.max_residual_kwh ?? '--' }} kWh
      </div>
    </div>

    <!-- Card 4: Anomaly Rate -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Anomaly Rate</span>
        <AlertTriangle class="w-3.5 h-3.5 text-status-amber" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span class="text-xl font-bold font-mono text-status-amber">{{ currentStats?.anomaly_rate_pct ?? '--' }}%</span>
        <span class="text-xs text-cockpit-300 font-mono">of samples</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        {{ currentStats?.anomaly_count ?? 0 }} observations flagged
      </div>
    </div>

    <!-- Card 5: Persistence Events -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Event Clusters</span>
        <Layers class="w-3.5 h-3.5 text-cockpit-300" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span class="text-xl font-bold font-mono text-cockpit-100">{{ currentStats?.event_count ?? '--' }}</span>
        <span class="text-xs text-cockpit-300 font-mono">events</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        Grouped sustained deviations
      </div>
    </div>

    <!-- Card 6: Approximate COP Efficiency -->
    <div class="bg-cockpit-900 border border-cockpit-800/80 rounded-lg p-3.5 hover:border-cockpit-700 transition-colors">
      <div class="flex items-center justify-between text-cockpit-300 text-xs mb-1">
        <span class="uppercase tracking-wider font-mono text-[10.5px]">Estimated COP</span>
        <Gauge class="w-3.5 h-3.5 text-status-emerald" />
      </div>
      <div class="flex items-baseline space-x-1.5">
        <span class="text-xl font-bold font-mono text-status-emerald">{{ currentStats?.avg_cop_approx ?? '--' }}</span>
        <span class="text-xs text-cockpit-300 font-mono">COP</span>
      </div>
      <div class="mt-1 text-[11px] text-cockpit-300">
        Thermal RT to Electrical kWh
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Activity, Cpu, TrendingUp, AlertTriangle, Layers, Gauge } from 'lucide-vue-next'

defineProps<{
  currentStats?: {
    avg_actual_kwh: number
    avg_expected_kwh: number
    avg_residual_kwh: number
    max_residual_kwh: number
    anomaly_count: number
    anomaly_rate_pct: number
    event_count: number
    avg_cop_approx: number
    total_records: number
  }
}>()
</script>
