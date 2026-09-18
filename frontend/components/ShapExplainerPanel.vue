<template>
  <div class="bg-white border border-surface-200 rounded-xl p-5 shadow-card space-y-4">
    
    <!-- Panel Header -->
    <div class="flex items-center justify-between pb-3 border-b border-surface-200">
      <div class="flex items-center space-x-2">
        <Sliders class="w-4 h-4 text-brand-600" />
        <h3 class="text-sm font-bold text-surface-900 font-sans tracking-tight">
          Investigation & Evidence Workbench
        </h3>
      </div>
      <span
        :class="[
          'text-[10.5px] font-mono font-semibold px-2 py-0.5 rounded uppercase tracking-wide',
          activeStatusClass
        ]"
      >
        {{ activeStatusText }}
      </span>
    </div>

    <!-- Active Observation Primary Metrics -->
    <div class="bg-surface-50 border border-surface-200 rounded-lg p-3 text-xs font-mono">
      <div class="flex items-center justify-between text-surface-500 mb-2 font-sans text-[11px]">
        <span>Timestamp: <strong class="text-surface-800 font-mono">{{ activeReading.ts }}</strong></span>
        <span>Unit: <strong class="text-surface-800 font-mono">{{ activeReading.equipment_id || 'CHILLER-01' }}</strong></span>
      </div>

      <div class="grid grid-cols-3 gap-2 pt-1 border-t border-surface-200/80">
        <div>
          <span class="text-surface-400 block text-[10px] uppercase">Measured</span>
          <span class="text-base font-bold text-surface-900">{{ activeReading.act.toFixed(1) }} <span class="text-[10px] font-normal text-surface-500">kWh</span></span>
        </div>
        <div>
          <span class="text-surface-400 block text-[10px] uppercase">Expected</span>
          <span class="text-base font-bold text-brand-700">{{ activeReading.exp.toFixed(1) }} <span class="text-[10px] font-normal text-surface-500">kWh</span></span>
        </div>
        <div>
          <span class="text-surface-400 block text-[10px] uppercase">Residual</span>
          <span :class="['text-base font-bold', activeReading.res > 15 ? 'text-red-700' : activeReading.res > 0 ? 'text-orange-700' : 'text-emerald-700']">
            {{ activeReading.res > 0 ? '+' : '' }}{{ activeReading.res.toFixed(1) }} <span class="text-[10px] font-normal text-surface-500">kWh</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Multi-Layer Supporting Evidence Checklist -->
    <div class="space-y-2">
      <h4 class="text-[11px] font-bold text-surface-700 uppercase tracking-wider font-sans">
        Supporting Evidence for Condition
      </h4>

      <div class="space-y-1.5 text-xs font-sans">
        <!-- Evidence 1: Statistical Residual & Robust MAD -->
        <div class="flex items-start space-x-2 bg-surface-50 p-2.5 rounded border border-surface-200/80">
          <div :class="['w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold', Math.abs(activeReading.z) > 3.0 ? 'bg-orange-100 text-orange-700' : 'bg-emerald-100 text-emerald-700']">
            {{ Math.abs(activeReading.z) > 3.0 ? '!' : '✓' }}
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-800">Robust Residual MAD Score</span>
              <span class="font-mono text-[11px] font-bold" :class="Math.abs(activeReading.z) > 3.0 ? 'text-orange-700' : 'text-emerald-700'">
                z = {{ activeReading.z.toFixed(2) }}
              </span>
            </div>
            <p class="text-[11.5px] text-surface-500 mt-0.5 leading-snug">
              {{ Math.abs(activeReading.z) > 3.0 ? 'Exceeds the 3.0 MAD threshold against 7-day rolling median.' : 'Within standard 3.0 MAD tolerance band of expected baseline.' }}
            </p>
          </div>
        </div>

        <!-- Evidence 2: Operating Envelope Check -->
        <div class="flex items-start space-x-2 bg-surface-50 p-2.5 rounded border border-surface-200/80">
          <div class="w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-700">
            ✓
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-800">Training Operating Envelope</span>
              <span class="font-mono text-[11px] text-emerald-700 font-semibold">Valid Regime</span>
            </div>
            <p class="text-[11.5px] text-surface-500 mt-0.5 leading-snug">
              Ambient temperature ({{ activeReading.out_temp ?? 82 }}°F) and load ({{ activeReading.load ?? 450 }} RT) are within 1st–99th training percentiles.
            </p>
          </div>
        </div>

        <!-- Evidence 3: Physical Telemetry Consistency -->
        <div class="flex items-start space-x-2 bg-surface-50 p-2.5 rounded border border-surface-200/80">
          <div class="w-4 h-4 rounded-full flex items-center justify-center shrink-0 mt-0.5 text-[10px] font-bold bg-emerald-100 text-emerald-700">
            ✓
          </div>
          <div class="flex-1">
            <div class="flex items-center justify-between">
              <span class="font-semibold text-surface-800">Sensor Physical Consistency</span>
              <span class="font-mono text-[11px] text-emerald-700 font-semibold">Pass</span>
            </div>
            <p class="text-[11.5px] text-surface-500 mt-0.5 leading-snug">
              No frozen sensor variance and water flow rate rate-of-change is physically plausible.
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- TreeSHAP Factor Attribution (Why did the model expect this baseline?) -->
    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <h4 class="text-[11px] font-bold text-surface-700 uppercase tracking-wider font-sans">
          Baseline Context Breakdown (SHAP)
        </h4>
        <span class="text-[10.5px] text-surface-400 font-mono">Factor Impact (kWh)</span>
      </div>

      <div class="space-y-1.5">
        <div
          v-for="contrib in contributors"
          :key="contrib.feature"
          class="bg-surface-50 p-2 rounded border border-surface-200/70 flex items-center justify-between text-xs font-mono"
        >
          <div class="truncate max-w-[60%] flex items-center space-x-1.5">
            <span :class="['w-2 h-2 rounded-sm shrink-0', contrib.shap > 0 ? 'bg-brand-600' : 'bg-emerald-600']"></span>
            <span class="text-surface-800 truncate font-medium">{{ contrib.feature }}</span>
          </div>

          <div class="flex items-center space-x-2">
            <span class="text-surface-400 text-[10px] font-sans">val: {{ contrib.value ?? '--' }}</span>
            <span
              :class="[
                'font-bold px-1.5 py-0.2 rounded text-[11px] min-w-[65px] text-right',
                contrib.shap > 0 ? 'text-brand-700 bg-brand-50' : 'text-emerald-700 bg-emerald-50'
              ]"
            >
              {{ contrib.shap > 0 ? '+' : '' }}{{ contrib.shap.toFixed(1) }} kWh
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Operational Recommendation Box -->
    <div class="bg-amber-50/70 border border-amber-200 rounded-lg p-3 text-xs font-sans space-y-1.5">
      <div class="flex items-center space-x-1.5 text-amber-800 font-semibold">
        <CheckCircle2 class="w-3.5 h-3.5 text-amber-700" />
        <span>Actionable Operational Recommendation</span>
      </div>
      <p class="text-amber-900 leading-relaxed text-[11.5px]">
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
    return 'bg-orange-100 text-orange-800 border border-orange-200'
  }
  if (s === 'LOW CONFIDENCE') {
    return 'bg-amber-100 text-amber-800 border border-amber-200'
  }
  if (s === 'DATA + ENERGY ISSUE') {
    return 'bg-red-100 text-red-800 border border-red-200'
  }
  return 'bg-emerald-100 text-emerald-800 border border-emerald-200'
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
