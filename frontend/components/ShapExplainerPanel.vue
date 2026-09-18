<template>
  <div class="bg-cockpit-900 border border-cockpit-800 rounded-lg p-4">
    <div class="flex items-center justify-between pb-3 border-b border-cockpit-800/60 mb-3">
      <div class="flex items-center space-x-2">
        <Sparkles class="w-4 h-4 text-status-blue" />
        <h3 class="text-sm font-semibold text-cockpit-100 font-sans">
          CatBoost TreeSHAP Attribution & Contextual Diagnostics
        </h3>
      </div>
      <span class="text-[11px] font-mono px-2 py-0.5 rounded bg-status-blue/10 text-status-blue border border-status-blue/20">
        Exact Shapley Values
      </span>
    </div>

    <!-- Active Reading Summary Card -->
    <div v-if="selectedPoint" class="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3 bg-cockpit-850 p-2.5 rounded border border-cockpit-750 text-xs font-mono">
      <div>
        <span class="text-cockpit-300 block text-[10px]">Timestamp</span>
        <span class="text-cockpit-100 font-medium">{{ selectedPoint.ts || selectedPoint.timestamp }}</span>
      </div>
      <div>
        <span class="text-cockpit-300 block text-[10px]">Actual / Expected</span>
        <span class="text-cockpit-100 font-medium">
          <span class="text-status-crimson">{{ selectedPoint.act || selectedPoint.actual_energy }}</span> / 
          <span class="text-status-blue">{{ selectedPoint.exp || selectedPoint.expected_energy }} kWh</span>
        </span>
      </div>
      <div>
        <span class="text-cockpit-300 block text-[10px]">Deviation (Residual)</span>
        <span :class="['font-bold', (selectedPoint.res || selectedPoint.residual) > 0 ? 'text-status-amber' : 'text-status-emerald']">
          {{ (selectedPoint.res || selectedPoint.residual) > 0 ? '+' : '' }}{{ selectedPoint.res || selectedPoint.residual }} kWh
        </span>
      </div>
      <div>
        <span class="text-cockpit-300 block text-[10px]">Diagnosis</span>
        <span :class="['font-semibold', (selectedPoint.anom === 1 || selectedPoint.residual > 10) ? 'text-status-amber' : 'text-status-emerald']">
          {{ (selectedPoint.anom === 1 || selectedPoint.residual > 10) ? '⚠️ INVESTIGATE' : '✅ NOMINAL' }}
        </span>
      </div>
    </div>

    <!-- Narrative Explanation Box -->
    <div class="bg-cockpit-950 p-3 rounded border border-cockpit-800 text-xs leading-relaxed text-cockpit-100 mb-4 font-sans">
      <div class="flex items-start space-x-2">
        <Info class="w-4 h-4 text-status-blue shrink-0 mt-0.5" />
        <div>
          <span class="font-semibold text-status-blue">Automated Diagnostic Narrative:</span>
          <p class="mt-1 text-cockpit-300">
            {{ narrativeText }}
          </p>
        </div>
      </div>
    </div>

    <!-- SHAP Attribution Horizontal Bars -->
    <div class="space-y-2">
      <div class="text-[11px] font-mono text-cockpit-300 uppercase tracking-wider mb-1 flex justify-between">
        <span>Operating Feature</span>
        <span>Impact on Expected Energy (kWh)</span>
      </div>

      <div
        v-for="contrib in contributors"
        :key="contrib.feature"
        class="bg-cockpit-850 p-2 rounded border border-cockpit-800/80 flex items-center justify-between text-xs font-mono"
      >
        <div class="flex items-center space-x-2 truncate max-w-[50%]">
          <span class="w-1.5 h-1.5 rounded-full" :class="contrib.shap > 0 ? 'bg-status-crimson' : 'bg-status-blue'"></span>
          <span class="text-cockpit-100 truncate">{{ contrib.feature }}</span>
        </div>

        <div class="flex items-center space-x-3">
          <span class="text-cockpit-300 text-[11px]">val: {{ contrib.value ?? '--' }}</span>
          <span
            :class="[
              'font-bold px-1.5 py-0.5 rounded text-[11px] min-w-[70px] text-right',
              contrib.shap > 0 ? 'text-status-crimson bg-status-crimson/10' : 'text-status-blue bg-status-blue/10'
            ]"
          >
            {{ contrib.shap > 0 ? '+' : '' }}{{ contrib.shap }} kWh
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sparkles, Info } from 'lucide-vue-next'

const props = defineProps<{
  selectedPoint?: any
  shapSamples?: Array<any>
}>()

const matchedSample = computed(() => {
  if (!props.selectedPoint || !props.shapSamples || props.shapSamples.length === 0) {
    return props.shapSamples?.[0] || null
  }
  const ts = props.selectedPoint.ts || props.selectedPoint.timestamp
  return props.shapSamples.find((s) => s.timestamp === ts) || props.shapSamples[0]
})

const narrativeText = computed(() => {
  if (matchedSample.value?.narrative) {
    return matchedSample.value.narrative
  }
  return 'CatBoost expected-energy baseline predicts power draw strictly from thermodynamic operating variables (Building Load, Flow Rate, Cooling Water Temperature, Outside Temperature & Wet Bulb). No label assumptions made.'
})

const contributors = computed(() => {
  if (matchedSample.value?.top_contributors) {
    return matchedSample.value.top_contributors
  }
  return [
    { feature: 'Building Load (RT)', shap: -9.9, value: '450.2', direction: 'decreases' },
    { feature: 'Cooling Water Temperature (C)', shap: 0.8, value: '31.2', direction: 'increases' },
    { feature: 'Chilled Water Rate (L/sec)', shap: -3.5, value: '92.4', direction: 'decreases' },
    { feature: 'hour_of_day', shap: -3.4, value: '2', direction: 'decreases' }
  ]
})
</script>
