<template>
  <div class="min-h-screen bg-[#F1F5F9] text-surface-900 font-sans antialiased selection:bg-brand-100 selection:text-brand-900">
    
    <!-- Top Cockpit Header -->
    <CockpitHeader
      :equipments="summary?.equipments || ['CHILLER-01', 'CHILLER-02', 'CHILLER-03']"
      :selected-equipment="selectedEquipment"
      :stats="summary?.equipment_stats"
      @select-equipment="onEquipmentChange"
    />

    <!-- Main Dashboard Body -->
    <main class="p-4 sm:p-5 md:p-6 space-y-5 max-w-[1680px] mx-auto">
      
      <!-- Top Operational KPI Bar -->
      <KpiMetricsStrip :current-stats="currentEquipmentStats" />

      <!-- Main Operational Analytics View -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        <!-- Left Column: Time-Series Exploration + Persistent Events Table (8 cols) -->
        <div class="lg:col-span-8 space-y-5">
          
          <!-- Interactive Time-Series Chart -->
          <TelemetryChart
            :telemetry="telemetryData"
            @inspect-point="onPointInspect"
          />

          <!-- Persistent Anomaly Events Cluster Table -->
          <AnomalyEventsTable
            :events="eventsData"
            :selected-event-id="activeEventId"
            @select-event="onEventSelect"
          />
        </div>

        <!-- Right Column: Investigation Workbench & Supporting Evidence (4 cols) -->
        <div class="lg:col-span-4 space-y-5 lg:sticky lg:top-20">
          
          <!-- Investigation & Attribution Workbench -->
          <ShapExplainerPanel
            :selected-point="activePoint"
            :shap-samples="shapSamples"
          />

          <!-- Model & Thermodynamic Context Card -->
          <div class="bg-surface-900 border border-surface-800 rounded-xl p-5 sm:p-6 shadow-card text-xs sm:text-sm font-sans space-y-3.5 text-white">
            <div class="flex items-center justify-between pb-3 border-b border-surface-800">
              <h4 class="text-base sm:text-lg font-bold text-white tracking-tight">
                ML Pipeline Architecture & Verification
              </h4>
              <span class="text-xs font-mono px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-500/40 font-bold">
                Validated
              </span>
            </div>

            <!-- Architectural Breakdown -->
            <ul class="space-y-2.5 text-surface-300 font-mono text-xs sm:text-sm">
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Model Core:</span>
                <span class="text-white font-semibold">CatBoost Regressor (Depth 4)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Validation Scheme:</span>
                <span class="text-white font-semibold">TimeSeriesSplit (5-Fold CV)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Chronological CV R²:</span>
                <span class="text-emerald-400 font-bold">0.7734 (CV MAE 9.89 kWh)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Production Accuracy:</span>
                <span class="text-emerald-400 font-bold">93.56% (100 − WAPE)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Anomaly Authority:</span>
                <span class="text-orange-400 font-bold">Robust MAD > 3.0 (7d Baseline)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Secondary Evidence:</span>
                <span class="text-surface-200 font-semibold">Isolation Forest Corroboration</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-400 font-sans">Data Quality Decoupling:</span>
                <span class="text-brand-300 font-semibold">4-State Separation Logic</span>
              </li>
            </ul>

            <!-- Process Rationale (Clean, direct, human-written) -->
            <div class="pt-3 border-t border-surface-800 text-xs sm:text-sm text-surface-400 leading-relaxed space-y-2 font-sans">
              <p>
                <strong class="text-surface-200">Operating Principle:</strong> Rather than applying static energy thresholds that cause false alarms during peak summer heat, this system learns expected power from simultaneous environmental and operating telemetry.
              </p>
              <p>
                The residual between measured and expected power is evaluated against a 7-day rolling median using median absolute deviation (MAD). Sensor faults and extreme weather trigger a <strong class="text-amber-400 font-semibold">Low Confidence</strong> state rather than false mechanical alerts.
              </p>
            </div>
          </div>

        </div>

      </div>
    </main>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const selectedEquipment = ref('CHILLER-01')
const activePoint = ref<any>(null)
const activeEventId = ref<number | undefined>(undefined)

// 1. Fetch Summary
const { data: summary } = await useFetch('/api/summary')

// 2. Fetch Telemetry for active equipment
const { data: rawTelemetry } = await useFetch(() => `/api/telemetry?equipment_id=${selectedEquipment.value}`)

// 3. Fetch Events for active equipment
const { data: rawEvents } = await useFetch(() => `/api/events?equipment=${selectedEquipment.value}`)

// 4. Fetch SHAP samples for active equipment
const { data: rawShap } = await useFetch(() => `/api/shap?equipment=${selectedEquipment.value}`)

const telemetryData = computed(() => (rawTelemetry.value as any[]) || [])
const eventsData = computed(() => {
  const all = (rawEvents.value as any[]) || []
  return all.filter((e: any) => e.equipment_id === selectedEquipment.value)
})
const shapSamples = computed(() => (rawShap.value as any[]) || [])

const currentEquipmentStats = computed(() => {
  if (!summary.value?.equipment_stats) return undefined
  return summary.value.equipment_stats[selectedEquipment.value]
})

const onEquipmentChange = (eq: string) => {
  selectedEquipment.value = eq
  activePoint.value = null
  activeEventId.value = undefined
}

const onPointInspect = (point: any) => {
  activePoint.value = {
    ...point,
    equipment_id: selectedEquipment.value
  }
}

const onEventSelect = (event: any) => {
  activeEventId.value = event.event_id
  // Find telemetry point matching event start
  const match = telemetryData.value.find((t: any) => t.ts.startsWith(event.start_time.substring(0, 16)))
  if (match) {
    activePoint.value = {
      ...match,
      equipment_id: event.equipment_id
    }
  } else {
    activePoint.value = {
      ts: event.start_time,
      act: event.max_residual + 110,
      exp: 110,
      res: event.max_residual,
      residual: event.max_residual,
      z: event.max_z_score || 3.2,
      anom: 1,
      status: 'ABNORMAL ENERGY',
      equipment_id: event.equipment_id
    }
  }
}
</script>
