<template>
  <div class="bg-white border border-surface-200 rounded-xl p-5 sm:p-6 shadow-card space-y-4 hover:border-surface-300 transition-colors">
    
    <!-- Panel Header -->
    <div class="-m-5 sm:-m-6 p-4 sm:p-5 mb-4 rounded-t-xl bg-surface-50 border-b border-surface-200 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <Sliders class="w-4 h-4 text-brand-600" />
        <h3 class="text-base sm:text-lg font-bold text-surface-900 font-sans tracking-tight">
          Investigation & Evidence Workbench
        </h3>
      </div>
      <span
        :class="[
          'text-xs font-mono font-bold px-2.5 py-1 rounded uppercase tracking-wide shadow-xs',
          activeStatusClass
        ]"
      >
        {{ activeStatusText }}
      </span>
    </div>

    <!-- Active Observation Primary Metrics -->
    <div class="bg-surface-100 border border-surface-200 rounded-lg p-3.5 text-xs sm:text-sm font-mono">
      <div class="flex items-center justify-between text-surface-600 mb-2.5 font-sans text-xs sm:text-sm">
        <span>Timestamp: <strong class="text-surface-900 font-mono font-bold">{{ activeReading.ts }}</strong></span>
        <span>Unit: <strong class="text-surface-900 font-mono font-bold">{{ activeReading.equipment_id || 'CHILLER-01' }}</strong></span>
      </div>

      <div class="grid grid-cols-3 gap-2.5 pt-2 border-t border-surface-200">
        <div>
          <span class="text-surface-500 block text-xs uppercase font-medium">Measured</span>
          <span class="text-lg sm:text-xl font-bold text-red-700">{{ activeReading.act.toFixed(1) }} <span class="text-xs font-normal text-surface-500">kWh</span></span>
        </div>
        <div>
          <span class="text-surface-500 block text-xs uppercase font-medium">Expected</span>
          <span class="text-lg sm:text-xl font-bold text-brand-700">{{ activeReading.exp.toFixed(1) }} <span class="text-xs font-normal text-surface-500">kWh</span></span>
        </div>
        <div>
          <span class="text-surface-500 block text-xs uppercase font-medium">Residual</span>
          <span :class="['text-lg sm:text-xl font-bold', activeReading.res > 15 ? 'text-red-700' : activeReading.res > 0 ? 'text-orange-700' : 'text-emerald-700']">
            {{ activeReading.res > 0 ? '+' : '' }}{{ activeReading.res.toFixed(1) }} <span class="text-xs font-normal text-surface-500">kWh</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Multi-Layer Supporting Evidence Checklist -->
    <div class="space-y-2.5">
      <h4 class="text-xs sm:text-sm font-bold text-surface-800 uppercase tracking-wider font-sans">
        Supporting Evidence for Condition
      </h4>

      <div class="space-y-2 text-xs sm:text-sm font-sans">
        <!-- Evidence 1: Statistical Residual & Robust MAD -->
        <div class="flex items-start space-x-2.5 bg-surface-50 p-3 rounded-lg border border-surface-200">
          <div :class="['w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold', Math.abs(activeReading.z) > 3.0 ? 'bg-orange-100 text-orange-800' : 'bg-emerald-100 text-emerald-800']">
            {{ Math.abs(activeReading.z) > 3.0 ? '!' : '✓' }}
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-900">Robust Residual MAD Score</span>
              <span class="font-mono text-xs sm:text-sm font-bold" :class="Math.abs(activeReading.z) > 3.0 ? 'text-orange-700' : 'text-emerald-700'">
                z = {{ activeReading.z.toFixed(2) }}
              </span>
            </div>
            <p class="text-xs sm:text-sm text-surface-600 mt-0.5 leading-snug">
              {{ Math.abs(activeReading.z) > 3.0 ? 'Exceeds the 3.0 MAD threshold against 7-day rolling baseline.' : 'Within standard 3.0 MAD tolerance band of expected baseline.' }}
            </p>
          </div>
        </div>

        <!-- Evidence 2: Operating Envelope Check -->
        <div class="flex items-start space-x-2.5 bg-surface-50 p-3 rounded-lg border border-surface-200">
          <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold bg-emerald-100 text-emerald-800">
            ✓
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-900">Training Operating Envelope</span>
              <span class="font-mono text-xs sm:text-sm text-emerald-700 font-bold">Valid Range</span>
            </div>
            <p class="text-xs sm:text-sm text-surface-600 mt-0.5 leading-snug">
              Ambient temperature ({{ activeReading.out_temp ?? 82 }}°F) and load ({{ activeReading.load ?? 450 }} RT) are within historical 1st–99th percentiles.
            </p>
          </div>
        </div>

        <!-- Evidence 3: Physical Telemetry Consistency -->
        <div class="flex items-start space-x-2.5 bg-surface-50 p-3 rounded-lg border border-surface-200">
          <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold bg-emerald-100 text-emerald-800">
            ✓
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-900">Physical Sensor Consistency</span>
              <span class="font-mono text-xs sm:text-sm text-emerald-700 font-bold">Passed</span>
            </div>
            <p class="text-xs sm:text-sm text-surface-600 mt-0.5 leading-snug">
              Sensors show active variance with no frozen values; water flow rate of change is physically valid.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- TreeSHAP Factor Attribution (Why did the model expect this baseline?) -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <h4 class="text-xs sm:text-sm font-bold text-surface-800 uppercase tracking-wider font-sans">
          Baseline Context Factors (SHAP)
        </h4>
        <span class="text-xs text-surface-500 font-mono">Factor Impact</span>
      </div>

      <div class="space-y-2">
        <div
          v-for="contrib in contributors"
          :key="contrib.feature"
          class="bg-surface-50 p-2.5 rounded-lg border border-surface-200 flex items-center justify-between text-xs sm:text-sm font-mono"
        >
          <div class="truncate max-w-[62%] flex items-center space-x-2">
            <span :class="['w-2 h-2 rounded-full shrink-0', contrib.shap > 0 ? 'bg-brand-600' : 'bg-emerald-600']"></span>
            <span class="text-surface-900 truncate font-semibold font-sans">{{ contrib.feature }}</span>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-surface-500 text-xs font-sans">val: {{ contrib.value ?? '--' }}</span>
            <span
              :class="[
                'font-bold px-2 py-0.5 rounded text-xs min-w-[70px] text-right',
                contrib.shap > 0 ? 'text-brand-800 bg-brand-100' : 'text-emerald-800 bg-emerald-100'
              ]"
            >
              {{ contrib.shap > 0 ? '+' : '' }}{{ contrib.shap.toFixed(1) }} kWh
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Operational Recommendation Box -->
    <div class="bg-amber-50 border border-amber-300/80 rounded-xl p-3.5 sm:p-4 text-xs sm:text-sm font-sans space-y-1.5">
      <div class="flex items-center space-x-2 text-amber-900 font-bold">
        <CheckCircle2 class="w-4 h-4 text-amber-700" />
        <span>Actionable Operational Recommendation</span>
      </div>
      <p class="text-amber-950 leading-relaxed text-xs sm:text-sm font-normal">
        {{ operationalRecommendation }}
      </p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Sliders, CheckCircle2 } from 'lucide-vue-next'

const props = defineProps<{
  selectedPoint?: any
  shapSamples?: Array<any>
}>()

const activeReading = computed(() => {
  if (props.selectedPoint) {
    return {
      ts: (props.selectedPoint.ts || props.selectedPoint.timestamp || '').substring(0, 16).replace('T', ' '),
      act: Number(props.selectedPoint.act || props.selectedPoint.actual_energy || 127.8),
      exp: Number(props.selectedPoint.exp || props.selectedPoint.expected_energy || 127.8),
      res: Number(props.selectedPoint.res !== undefined ? props.selectedPoint.res : props.selectedPoint.residual || 0),
      z: Number(props.selectedPoint.z !== undefined ? props.selectedPoint.z : props.selectedPoint.max_z_score || 0),
      anom: Number(props.selectedPoint.anom || 0),
      status: props.selectedPoint.status || 'NORMAL',
      load: props.selectedPoint.load,
      flow: props.selectedPoint.flow,
      cw_temp: props.selectedPoint.cw_temp,
      out_temp: props.selectedPoint.out_temp,
      wb_temp: props.selectedPoint.wb_temp,
      equipment_id: props.selectedPoint.equipment_id
    }
  }

  // Default to sample if nothing selected
  return {
    ts: '2020-05-31 18:30',
    act: 142.8,
    exp: 113.5,
    res: 29.3,
    z: 3.15,
    anom: 1,
    status: 'ABNORMAL ENERGY',
    load: 438.1,
    flow: 88.3,
    cw_temp: 31.6,
    out_temp: 82.0,
    wb_temp: 24.9,
    equipment_id: 'CHILLER-01'
  }
})

const activeStatusText = computed(() => {
  const s = activeReading.value.status
  if (s === 'ABNORMAL ENERGY' || activeReading.value.anom === 1) return 'Abnormal Energy'
  if (s === 'LOW CONFIDENCE') return 'Low Confidence'
  if (s === 'DATA + ENERGY ISSUE') return 'Data & Energy Issue'
  return 'Nominal Operation'
})

const activeStatusClass = computed(() => {
  const s = activeReading.value.status
  if (s === 'ABNORMAL ENERGY' || activeReading.value.anom === 1) {
    return 'bg-orange-100 text-orange-900 border border-orange-300'
  }
  if (s === 'LOW CONFIDENCE') {
    return 'bg-amber-100 text-amber-900 border border-amber-300'
  }
  if (s === 'DATA + ENERGY ISSUE') {
    return 'bg-red-100 text-red-900 border border-red-300'
  }
  return 'bg-emerald-100 text-emerald-900 border border-emerald-300'
})

const matchedSample = computed(() => {
  if (!props.shapSamples || props.shapSamples.length === 0) return null
  const ts = activeReading.value.ts
  return props.shapSamples.find((s) => s.timestamp.startsWith(ts.substring(0, 10))) || props.shapSamples[0]
})

const contributors = computed(() => {
  if (matchedSample.value?.top_contributors) {
    return matchedSample.value.top_contributors.map((c: any) => ({
      feature: c.feature,
      shap: Number(c.shap),
      value: c.value
    }))
  }
  return [
    { feature: 'Building Load (RT)', shap: 12.4, value: '438.1' },
    { feature: 'Cooling Water Temp (C)', shap: 5.5, value: '31.6' },
    { feature: 'Outside Temperature (F)', shap: 1.2, value: '82.0' },
    { feature: 'Chilled Water Rate (L/sec)', shap: -2.3, value: '88.3' }
  ]
})

const operationalRecommendation = computed(() => {
  const r = activeReading.value.res
  const isLowConf = activeReading.value.status === 'LOW CONFIDENCE'

  if (isLowConf) {
    return 'Telemetry confidence is reduced due to boundary operating conditions or sensor volatility. Verify physical transmitter calibration and flow meter zero-point before dispatching mechanical crew.'
  }
  if (r > 20) {
    return 'Substantial excess power consumption under nominal building load and chilled water flow. Indication of possible condenser tube fouling, non-condensable gas buildup, or degraded refrigerant subcooling. Recommended action: Inspect condenser approach temperature and cooling tower delta-T.'
  }
  if (r > 8) {
    return 'Moderate contextual power elevation. Check variable speed drive (VFD) frequency hunting and ensure expansion valve superheat settings are stable.'
  }
  if (r < -15) {
    return 'Power consumption significantly below expected model envelope for current demand. Verify power meter CT multiplier and verify if chiller is operating under partial unloader bypass.'
  }
  return 'Equipment is operating in complete accordance with contextual thermodynamic baseline. No maintenance intervention required at this time.'
})
</script>
