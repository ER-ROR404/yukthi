<template>
  <header class="bg-white border-b border-surface-200 px-6 py-4 sticky top-0 z-30 shadow-subtle">
    <div class="max-w-[1680px] mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      
      <!-- Brand & Facility Identity -->
      <div class="flex items-center space-x-3.5">
        <div class="h-10 w-10 rounded-lg bg-surface-900 flex items-center justify-center text-white shadow-card">
          <Activity class="w-5 h-5 text-brand-500" />
        </div>
        <div>
          <div class="flex items-center space-x-2.5">
            <span class="font-bold text-lg sm:text-xl text-surface-900 tracking-tight font-sans">
              YUKTHI
            </span>
            <span class="text-xs px-2.5 py-0.5 rounded font-medium bg-surface-100 border border-surface-200 text-surface-700">
              Chiller Energy Intelligence
            </span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              <span class="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
              Live Telemetry
            </span>
          </div>
          <p class="text-xs sm:text-sm text-surface-600 mt-0.5 font-sans">
            Contextual Expected-Energy Baseline & Robust Anomaly Analytics
          </p>
        </div>
      </div>

      <!-- Equipment Selector Tabs -->
      <div class="flex items-center space-x-2 bg-surface-100 p-1.5 rounded-lg border border-surface-200">
        <button
          v-for="eq in equipments"
          :key="eq"
          @click="$emit('select-equipment', eq)"
          :class="[
            'px-4 py-2 rounded-md text-xs sm:text-sm font-mono font-semibold transition-all duration-150 flex items-center space-x-2 cursor-pointer',
            selectedEquipment === eq
              ? 'bg-white text-surface-900 shadow-sm border border-surface-200/90 font-bold'
              : 'text-surface-600 hover:text-surface-900 hover:bg-surface-200/60'
          ]"
        >
          <span>{{ eq }}</span>
          <span
            v-if="stats && stats[eq]"
            :class="[
              'text-xs px-2 py-0.5 rounded font-mono font-medium',
              stats[eq].anomaly_count > 0
                ? 'bg-amber-100 text-amber-900 border border-amber-300/60'
                : 'bg-emerald-100 text-emerald-900'
            ]"
          >
            {{ stats[eq].anomaly_count }} alerts
          </span>
        </button>
      </div>

      <!-- Validated Model Performance Specs -->
      <div class="hidden lg:flex items-center space-x-6 border-l border-surface-200 pl-6 text-xs sm:text-sm font-mono">
        <div>
          <span class="text-surface-500 block text-xs uppercase tracking-wider font-sans font-medium">Cross-Validation</span>
          <span class="text-emerald-700 font-bold text-sm sm:text-base">92.5% Acc <span class="text-surface-500 font-normal text-xs">(R² 0.77)</span></span>
        </div>
        <div>
          <span class="text-surface-500 block text-xs uppercase tracking-wider font-sans font-medium">Mean Deviation</span>
          <span class="text-surface-900 font-bold text-sm sm:text-base">MAE 8.4 kWh</span>
        </div>
        <div>
          <span class="text-surface-500 block text-xs uppercase tracking-wider font-sans font-medium">Grid Interval</span>
          <span class="text-surface-800 font-semibold text-sm sm:text-base">30 Minutes</span>
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
