<template>
  <header class="bg-white border-b border-surface-200 px-6 py-3.5 sticky top-0 z-30 shadow-subtle">
    <div class="max-w-[1680px] mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      
      <!-- Brand & Facility Identity -->
      <div class="flex items-center space-x-3.5">
        <div class="h-9 w-9 rounded-lg bg-surface-900 flex items-center justify-center text-white shadow-card">
          <Activity class="w-4 h-4 text-brand-500" />
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <span class="font-bold text-base text-surface-900 tracking-tight font-sans">
              YUKTHI
            </span>
            <span class="text-xs px-2 py-0.5 rounded bg-surface-100 border border-surface-200 text-surface-600 font-medium">
              Chiller Energy Intelligence
            </span>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5"></span>
              Online Telemetry
            </span>
          </div>
          <p class="text-xs text-surface-500 mt-0.5">
            Contextual Expected-Energy Baselines • Robust Residual Anomaly Detection
          </p>
        </div>
      </div>

      <!-- Equipment Selector Tabs -->
      <div class="flex items-center space-x-1.5 bg-surface-100 p-1 rounded-lg border border-surface-200">
        <button
          v-for="eq in equipments"
          :key="eq"
          @click="$emit('select-equipment', eq)"
          :class="[
            'px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150 flex items-center space-x-2 cursor-pointer',
            selectedEquipment === eq
              ? 'bg-white text-surface-900 shadow-sm border border-surface-200/80 font-semibold'
              : 'text-surface-600 hover:text-surface-900 hover:bg-surface-200/60'
          ]"
        >
          <span>{{ eq }}</span>
          <span
            v-if="stats && stats[eq]"
            :class="[
              'text-[10.5px] px-1.5 py-0.2 rounded font-mono',
              stats[eq].anomaly_count > 0
                ? 'bg-amber-50 text-amber-700 border border-amber-200/60'
                : 'bg-emerald-50 text-emerald-700'
            ]"
          >
            {{ stats[eq].anomaly_count }} alerts
          </span>
        </button>
      </div>

      <!-- Validated Model Performance Specs -->
      <div class="hidden lg:flex items-center space-x-5 border-l border-surface-200 pl-5 text-xs font-mono">
        <div>
          <span class="text-surface-400 block text-[10px] uppercase tracking-wider font-sans font-medium">Chronological CV</span>
          <span class="text-emerald-700 font-semibold">92.5% Acc <span class="text-surface-400 font-normal">(R² 0.77)</span></span>
        </div>
        <div>
          <span class="text-surface-400 block text-[10px] uppercase tracking-wider font-sans font-medium">Mean Deviation</span>
          <span class="text-surface-800 font-semibold">MAE 8.4 kWh</span>
        </div>
        <div>
          <span class="text-surface-400 block text-[10px] uppercase tracking-wider font-sans font-medium">Nominal Sampling</span>
          <span class="text-surface-700 font-medium">30-min grid</span>
        </div>
      </div>

    </div>
  </header>
</template>

<script setup lang="ts">
import { Activity } from 'lucide-vue-next'

defineProps<{
  equipments: string[]
  selectedEquipment: string
  stats?: Record<string, any>
}>()

defineEmits<{
  (e: 'select-equipment', eq: string): void
}>()
</script>
