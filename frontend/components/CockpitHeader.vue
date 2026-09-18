<template>
  <header class="border-b border-cockpit-800 bg-cockpit-950/80 backdrop-blur px-6 py-4 sticky top-0 z-30">
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
      <!-- Title & Branding -->
      <div class="flex items-center space-x-3">
        <div class="h-9 w-9 rounded-lg bg-status-blue/10 border border-status-blue/30 flex items-center justify-center text-status-blue shadow-[0_0_15px_rgba(59,130,246,0.2)]">
          <Zap class="w-5 h-5" />
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="font-bold text-lg text-cockpit-100 tracking-tight font-sans">
              YUKTHI <span class="text-xs px-2 py-0.5 rounded bg-cockpit-800 border border-cockpit-700 text-cockpit-300 font-mono font-medium uppercase tracking-wider">Contextual Chiller Intelligence</span>
            </h1>
            <span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
              ISA-101 Active
            </span>
          </div>
          <p class="text-xs text-cockpit-300 mt-0.5">
            Physics-Informed Expected-Energy Baseline & Robust Anomaly Engine
          </p>
        </div>
      </div>

      <!-- Equipment Selector Tabs -->
      <div class="flex items-center space-x-2 bg-cockpit-900 p-1.5 rounded-lg border border-cockpit-800">
        <button
          v-for="eq in equipments"
          :key="eq"
          @click="$emit('select-equipment', eq)"
          :class="[
            'px-3.5 py-1.5 rounded-md text-xs font-mono font-medium transition-all duration-150 flex items-center space-x-2 cursor-pointer',
            selectedEquipment === eq
              ? 'bg-status-blue text-white shadow-[0_0_12px_rgba(59,130,246,0.3)] font-semibold'
              : 'text-cockpit-300 hover:text-cockpit-100 hover:bg-cockpit-800'
          ]"
        >
          <span>{{ eq }}</span>
          <span
            v-if="stats && stats[eq]"
            :class="[
              'text-[10px] px-1.5 py-0.2 rounded-full font-mono',
              selectedEquipment === eq
                ? 'bg-blue-950/60 text-blue-200'
                : 'bg-cockpit-800 text-cockpit-300'
            ]"
          >
            {{ stats[eq].anomaly_rate_pct }}% dev
          </span>
        </button>
      </div>

      <!-- Quick Metrics Badge -->
      <div class="hidden lg:flex items-center space-x-4 border-l border-cockpit-800 pl-4 text-xs font-mono">
        <div>
          <span class="text-cockpit-300 block text-[10px] uppercase tracking-wider">Model R²</span>
          <span class="text-status-emerald font-semibold">0.7727 (CV 5-fold)</span>
        </div>
        <div>
          <span class="text-cockpit-300 block text-[10px] uppercase tracking-wider">CV MAE</span>
          <span class="text-cockpit-100 font-semibold">9.92 kWh</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Zap } from 'lucide-vue-next'

defineProps<{
  equipments: string[]
  selectedEquipment: string
  stats?: Record<string, any>
}>()

defineEmits<{
  (e: 'select-equipment', eq: string): void
}>()
</script>
