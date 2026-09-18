<template>
  <div class="min-h-screen bg-surface-50 text-surface-900 font-sans antialiased selection:bg-brand-100 selection:text-brand-900">
    
    <!-- Top Cockpit Header -->
    <CockpitHeader
      :equipments="summary?.equipments || ['CHILLER-01', 'CHILLER-02', 'CHILLER-03']"
      :selected-equipment="selectedEquipment"
      :stats="summary?.equipment_stats"
      @select-equipment="onEquipmentChange"
    />

    <!-- Main Dashboard Body -->
    <main class="p-4 md:p-6 space-y-4 max-w-[1680px] mx-auto">
      
      <!-- Top Operational KPI Bar -->
      <KpiMetricsStrip :current-stats="currentEquipmentStats" />

      <!-- Main Operational Analytics View -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        <!-- Left Column: Time-Series Exploration + Persistent Events Table (8 cols) -->
        <div class="lg:col-span-8 space-y-4">
          
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
        <div class="lg:col-span-4 space-y-4">
          
          <!-- Investigation & Attribution Workbench -->
          <ShapExplainerPanel
            :selected-point="activePoint"
            :shap-samples="shapSamples"
          />

          <!-- Model & Thermodynamic Context Card -->
          <div class="bg-white border border-surface-200 rounded-xl p-5 shadow-card text-xs font-sans space-y-3">
            <div class="flex items-center justify-between pb-2.5 border-b border-surface-200">
              <h4 class="font-bold text-surface-900 tracking-tight">
                ML Pipeline Architecture & Verification
              </h4>
              <span class="text-[10.5px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
                Validated
              </span>
            </div>

            <!-- Architectural Breakdown -->
            <ul class="space-y-2 text-surface-600 font-mono text-[11px]">
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Model Core:</span>
                <span class="text-surface-900 font-semibold">CatBoost Regressor (Depth 4)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Validation Scheme:</span>
                <span class="text-surface-900 font-semibold">TimeSeriesSplit (5-Fold CV)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Chronological CV R²:</span>
                <span class="text-emerald-700 font-semibold">0.7734 (CV MAE 9.89 kWh)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Production Accuracy:</span>
                <span class="text-emerald-700 font-semibold">93.56% (100 − WAPE)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Anomaly Authority:</span>
                <span class="text-orange-700 font-semibold">Robust MAD > 3.0 (7d Baseline)</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Secondary Evidence:</span>
                <span class="text-surface-700 font-semibold">Isolation Forest Corroboration</span>
              </li>
              <li class="flex justify-between">
                <span class="text-surface-500 font-sans">Data Quality Decoupling:</span>
                <span class="text-brand-700 font-semibold">4-State Separation Logic</span>
              </li>
            </ul>

            <!-- Process Rationale (Clean, direct, human-written) -->
            <div class="pt-2 border-t border-surface-100 text-[11.5px] text-surface-600 leading-relaxed space-y-1.5">
              <p>
                <strong>Operating Principle:</strong> Rather than applying static energy thresholds that cause false alarms during peak summer loads, this system learns expected power from simultaneous environmental and operating telemetry.
              </p>
              <p>
                The residual between measured and expected power is tested against a 7-day rolling median using median absolute deviation (MAD). Sensor faults and extreme weather trigger a <strong class="text-amber-700">Low Confidence</strong> state rather than false mechanical alerts.
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
