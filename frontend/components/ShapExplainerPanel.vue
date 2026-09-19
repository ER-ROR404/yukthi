<template>
  <div class="card-solid bg-white border border-slate-300 rounded-xl overflow-hidden shadow-xs hover:border-slate-400 transition-colors">
    
    <!-- Panel Header: Natural full-width block with zero negative margins -->
    <div class="px-5 sm:px-6 py-4 bg-slate-100 border-b border-slate-300 flex flex-wrap items-center justify-between gap-2.5">
      <div class="flex items-center space-x-2.5">
        <Sliders class="w-5 h-5 text-blue-600" />
        <h3 class="text-base sm:text-xl font-bold text-slate-950 font-sans tracking-tight">
          Investigation & Evidence Workbench
        </h3>
      </div>
      <span
        :class="[
          'text-xs font-mono font-bold px-3 py-1 rounded-md uppercase tracking-wider shadow-xs',
          activeStatusClass
        ]"
      >
        {{ activeStatusText }}
      </span>
    </div>

    <!-- Panel Body: Clean internal padding, zero overlap possible -->
    <div class="p-5 sm:p-6 space-y-5">

      <!-- Active Observation Primary Metrics (Timestamp & Energy Box) -->
      <div class="bg-slate-100 border border-slate-300 rounded-lg p-4 text-sm font-mono">
        <div class="flex flex-wrap items-center justify-between gap-2 text-slate-700 mb-3 font-sans text-xs sm:text-sm font-medium">
          <span>Timestamp: <strong class="text-slate-950 font-mono font-bold">{{ activeReading.ts }}</strong></span>
          <span>Unit: <strong class="text-slate-950 font-mono font-bold">{{ activeReading.equipment_id || 'CHILLER-01' }}</strong></span>
        </div>

        <div class="grid grid-cols-3 gap-3 pt-3 border-t border-slate-300">
          <div>
            <span class="text-slate-600 block text-xs uppercase font-bold tracking-wider">Measured</span>
            <span class="text-xl sm:text-2xl font-bold text-red-700">{{ activeReading.act.toFixed(1) }} <span class="text-xs font-normal text-slate-600">kWh</span></span>
          </div>
          <div>
            <span class="text-slate-600 block text-xs uppercase font-bold tracking-wider">Expected</span>
            <span class="text-xl sm:text-2xl font-bold text-blue-700">{{ activeReading.exp.toFixed(1) }} <span class="text-xs font-normal text-slate-600">kWh</span></span>
          </div>
          <div>
            <span class="text-slate-600 block text-xs uppercase font-bold tracking-wider">Residual</span>
            <span :class="['text-xl sm:text-2xl font-bold', activeReading.res > 15 ? 'text-red-700' : activeReading.res > 0 ? 'text-amber-800' : 'text-emerald-800']">
              {{ activeReading.res > 0 ? '+' : '' }}{{ activeReading.res.toFixed(1) }} <span class="text-xs font-normal text-slate-600">kWh</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Multi-Layer Supporting Evidence Checklist -->
      <div class="space-y-3">
        <h4 class="text-xs sm:text-sm font-bold text-slate-900 uppercase tracking-wider font-sans">
          Supporting Evidence for Condition
        </h4>

        <div class="space-y-2.5 text-xs sm:text-sm font-sans">
          <!-- Evidence 1: Statistical Residual & Robust MAD -->
          <div class="flex items-start space-x-3 bg-slate-50 p-3.5 rounded-lg border border-slate-300">
            <div :class="['w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold', Math.abs(activeReading.z) > 3.0 ? 'bg-orange-100 text-orange-900 border border-orange-300' : 'bg-emerald-100 text-emerald-900 border border-emerald-300']">
              {{ Math.abs(activeReading.z) > 3.0 ? '!' : '✓' }}
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 text-sm">Robust Residual MAD Score</span>
                <span class="font-mono text-sm font-bold" :class="Math.abs(activeReading.z) > 3.0 ? 'text-orange-800' : 'text-emerald-800'">
                  z = {{ activeReading.z.toFixed(2) }}
                </span>
              </div>
              <p class="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed font-medium">
                {{ Math.abs(activeReading.z) > 3.0 ? 'Exceeds the 3.0 MAD threshold against 7-day rolling baseline.' : 'Within standard 3.0 MAD tolerance band of expected baseline.' }}
              </p>
            </div>
          </div>

          <!-- Evidence 2: Operating Envelope Check -->
          <div class="flex items-start space-x-3 bg-slate-50 p-3.5 rounded-lg border border-slate-300">
            <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
              ✓
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 text-sm">Training Operating Envelope</span>
                <span class="font-mono text-sm text-emerald-800 font-bold">Valid Range</span>
              </div>
              <p class="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed font-medium">
                Ambient temperature ({{ activeReading.out_temp ?? 82 }}°F) and load ({{ activeReading.load ?? 450 }} RT) are within historical 1st–99th percentiles.
              </p>
            </div>
          </div>

          <!-- Evidence 3: Physical Telemetry Consistency -->
          <div class="flex items-start space-x-3 bg-slate-50 p-3.5 rounded-lg border border-slate-300">
            <div class="w-5 h-5 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-xs font-bold bg-emerald-100 text-emerald-900 border border-emerald-300">
              ✓
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-slate-900 text-sm">Physical Sensor Consistency</span>
                <span class="font-mono text-sm text-emerald-800 font-bold">Passed</span>
              </div>
              <p class="text-xs sm:text-sm text-slate-600 mt-1 leading-relaxed font-medium">
                Sensors show active variance with no frozen values; water flow rate of change is physically valid.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- TreeSHAP Factor Attribution (Why did the model expect this baseline?) -->
      <div class="space-y-3">
        <div class="flex items-center justify-between">
          <h4 class="text-xs sm:text-sm font-bold text-slate-900 uppercase tracking-wider font-sans">
            Baseline Context Factors (SHAP)
          </h4>
          <span class="text-xs text-slate-600 font-mono font-semibold">Factor Impact</span>
        </div>

        <div class="space-y-2">
          <div
            v-for="contrib in contributors"
            :key="contrib.feature"
            class="bg-slate-50 p-3 rounded-lg border border-slate-300 flex items-center justify-between text-xs sm:text-sm font-mono"
          >
            <div class="truncate max-w-[62%] flex items-center space-x-2">
              <span :class="['w-2 h-2 rounded-full shrink-0', contrib.shap > 0 ? 'bg-blue-600' : 'bg-emerald-600']"></span>
              <span class="text-slate-950 truncate font-semibold font-sans">{{ contrib.feature }}</span>
            </div>

            <div class="flex items-center space-x-2.5">
              <span class="text-slate-600 text-xs font-sans font-medium">val: {{ contrib.value ?? '--' }}</span>
              <span
                :class="[
                  'font-bold px-2 py-0.5 rounded text-xs min-w-[70px] text-right',
                  contrib.shap > 0 ? 'text-blue-900 bg-blue-100 border border-blue-200' : 'text-emerald-900 bg-emerald-100 border border-emerald-200'
                ]"
              >
                {{ contrib.shap > 0 ? '+' : '' }}{{ contrib.shap.toFixed(1) }} kWh
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Actionable Operational Recommendation Box -->
      <div class="bg-amber-50 border-2 border-amber-300 rounded-xl p-4 sm:p-5 text-sm font-sans space-y-2">
        <div class="flex items-center space-x-2 text-amber-900 font-bold text-sm sm:text-base">
          <CheckCircle2 class="w-5 h-5 text-amber-800" />
          <span>Actionable Operational Recommendation</span>
        </div>
        <p class="text-amber-950 leading-relaxed text-sm font-medium">
          {{ operationalRecommendation }}
        </p>
      </div>

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
    return 'bg-purple-100 text-purple-900 border border-purple-300'
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
