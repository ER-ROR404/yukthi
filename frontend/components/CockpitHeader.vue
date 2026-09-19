<template>
  <header class="bg-surface-900 border-b border-surface-800 px-5 sm:px-6 py-3.5 sm:py-4 sticky top-0 z-30 shadow-card text-white">
    <div class="max-w-[1680px] mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      
      <!-- Brand & Facility Identity -->
      <div class="flex items-center space-x-3.5">
        <div class="h-10 w-10 rounded-lg bg-surface-800 border border-surface-700 flex items-center justify-center text-white shadow-xs">
          <Activity class="w-5 h-5 text-brand-400" />
        </div>
        <div>
          <div class="flex items-center space-x-2.5">
            <span class="font-bold text-lg sm:text-xl text-white tracking-tight font-sans">
              YUKTHI
            </span>
            <span class="text-xs px-2.5 py-0.5 rounded font-medium bg-surface-800 border border-surface-700 text-surface-300 font-mono">
              Chiller Energy Intelligence
            </span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-300 border border-emerald-500/40">
              <span class="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
              Live Telemetry
            </span>
          </div>
          <p class="text-xs sm:text-sm text-surface-400 mt-0.5 font-sans">
            Contextual Expected-Energy Baseline & Robust Anomaly Analytics
          </p>
        </div>
      </div>

      <!-- Equipment Selector Tabs -->
      <div class="flex items-center space-x-2 bg-surface-800/90 p-1.5 rounded-lg border border-surface-700">
        <button
          v-for="eq in equipments"
          :key="eq"
          @click="$emit('select-equipment', eq)"
          :class="[
            'px-4 py-2 rounded-md text-xs sm:text-sm font-mono font-semibold transition-all duration-150 flex items-center space-x-2 cursor-pointer',
            selectedEquipment === eq
              ? 'bg-white text-surface-950 shadow-sm font-bold'
              : 'text-surface-300 hover:text-white hover:bg-surface-700/70'
          ]"
        >
          <span>{{ eq }}</span>
          <span
            v-if="stats && stats[eq]"
            :class="[
              'text-xs px-2 py-0.5 rounded font-mono font-medium',
              selectedEquipment === eq
                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                : 'bg-amber-900/50 text-amber-300 border border-amber-700/60'
            ]"
          >
            {{ stats[eq].anomaly_count }} alerts
          </span>
        </button>
      </div>

      <!-- Validated Model Performance Specs -->
      <div class="hidden lg:flex items-center space-x-6 border-l border-surface-800 pl-6 text-xs sm:text-sm font-mono">
        <div>
          <span class="text-surface-400 block text-xs uppercase tracking-wider font-sans font-medium">Cross-Validation</span>
          <span class="text-emerald-400 font-bold text-sm sm:text-base">92.5% Acc <span class="text-surface-400 font-normal text-xs">(R² 0.77)</span></span>
        </div>
        <div>
          <span class="text-surface-400 block text-xs uppercase tracking-wider font-sans font-medium">Mean Deviation</span>
          <span class="text-white font-bold text-sm sm:text-base">MAE 8.4 kWh</span>
        </div>
        <div>
          <span class="text-surface-400 block text-xs uppercase tracking-wider font-sans font-medium">Grid Interval</span>
          <span class="text-surface-200 font-semibold text-sm sm:text-base">30 Minutes</span>
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
