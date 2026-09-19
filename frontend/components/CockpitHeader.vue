<template>
  <header class="bg-slate-100 border-b border-slate-300 px-5 sm:px-6 py-3.5 sm:py-4 sticky top-0 z-30 shadow-xs text-slate-900">
    <div class="max-w-[1680px] mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      
      <!-- Brand & Facility Identity -->
      <div class="flex items-center space-x-3.5">
        <div class="h-10 w-10 rounded-lg bg-slate-900 text-white flex items-center justify-center shadow-xs">
          <Activity class="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <div class="flex items-center space-x-2.5">
            <span class="font-bold text-lg sm:text-xl text-slate-950 tracking-tight font-sans">
              YUKTHI
            </span>
            <span class="text-xs px-2.5 py-0.5 rounded font-semibold bg-white border border-slate-300 text-slate-800 font-mono shadow-xs">
              Chiller Energy Intelligence
            </span>
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300">
              <span class="w-2 h-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
              Live Telemetry
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-600 mt-0.5 font-sans font-medium">
            Contextual Expected-Energy Baseline & Robust Anomaly Analytics
          </p>
        </div>
      </div>

      <!-- Equipment Selector Tabs -->
      <div class="flex items-center space-x-2 bg-slate-200/80 p-1.5 rounded-lg border border-slate-300">
        <button
          v-for="eq in equipments"
          :key="eq"
          @click="$emit('select-equipment', eq)"
          :class="[
            'px-4 py-2 rounded-md text-xs sm:text-sm font-mono font-semibold transition-all duration-150 flex items-center space-x-2 cursor-pointer',
            selectedEquipment === eq
              ? 'bg-white text-slate-950 shadow-xs border border-slate-300 font-bold'
              : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
          ]"
        >
          <span>{{ eq }}</span>
          <span
            v-if="stats && stats[eq]"
            :class="[
              'text-xs px-2 py-0.5 rounded font-mono font-bold',
              selectedEquipment === eq
                ? 'bg-amber-100 text-amber-900 border border-amber-300'
                : 'bg-amber-50 text-amber-900 border border-amber-200'
            ]"
          >
            {{ stats[eq].anomaly_count }} alerts
          </span>
        </button>
      </div>

      <!-- Validated Model Performance Specs -->
      <div class="hidden lg:flex items-center space-x-6 border-l border-slate-300 pl-6 text-xs sm:text-sm font-mono">
        <div>
          <span class="text-slate-500 block text-xs uppercase tracking-wider font-sans font-semibold">Cross-Validation</span>
          <span class="text-emerald-700 font-bold text-sm sm:text-base">92.5% Acc <span class="text-slate-500 font-normal text-xs">(R² 0.77)</span></span>
        </div>
        <div>
          <span class="text-slate-500 block text-xs uppercase tracking-wider font-sans font-semibold">Mean Deviation</span>
          <span class="text-slate-900 font-bold text-sm sm:text-base">MAE 8.4 kWh</span>
        </div>
        <div>
          <span class="text-slate-500 block text-xs uppercase tracking-wider font-sans font-semibold">Grid Interval</span>
          <span class="text-slate-800 font-semibold text-sm sm:text-base">30 Minutes</span>
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
