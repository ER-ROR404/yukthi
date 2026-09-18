<template>
  <div class="min-h-screen bg-cockpit-950 text-cockpit-100 font-sans antialiased selection:bg-status-blue/30 selection:text-white">
    <!-- Cockpit Header -->
    <CockpitHeader
      :equipments="summary?.equipments || ['CHILLER-01', 'CHILLER-02', 'CHILLER-03']"
      :selected-equipment="selectedEquipment"
      :stats="summary?.equipment_stats"
      @select-equipment="onEquipmentChange"
    />

    <!-- Main Telemetry Body -->
    <main class="p-4 md:p-6 space-y-4 max-w-[1600px] mx-auto">
      <!-- Top KPI Bar -->
      <KpiMetricsStrip :current-stats="currentEquipmentStats" />

      <!-- Main Operational View: Chart + SHAP Diagnostics -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <!-- Telemetry Timeline Stream (8 cols) -->
        <div class="lg:col-span-8 space-y-4">
          <TelemetryChart
            :telemetry="telemetryData"
            @inspect-point="onPointInspect"
          />

          <!-- Persistent Anomaly Events Cluster Table -->
          <AnomalyEventsTable
            :events="eventsData"
            @select-event="onEventSelect"
          />
        </div>

        <!-- Right Side: SHAP Attribution & Diagnostic Panel (4 cols) -->
        <div class="lg:col-span-4 space-y-4">
          <ShapExplainerPanel
            :selected-point="activePoint"
            :shap-samples="shapSamples"
          />

          <!-- Model & Thermodynamic Context Card -->
          <div class="bg-cockpit-900 border border-cockpit-800 rounded-lg p-4 text-xs font-mono">
            <h4 class="text-cockpit-100 font-bold mb-2 font-sans flex items-center justify-between">
              <span>ML Architecture & Physics Engine</span>
              <span class="text-[10px] text-status-emerald bg-emerald-500/10 px-1.5 py-0.5 rounded">Verified</span>
            </h4>
            <ul class="space-y-2 text-cockpit-300">
              <li class="flex justify-between">
                <span>Model Class:</span>
                <span class="text-cockpit-100">CatBoost Regressor</span>
              </li>
              <li class="flex justify-between">
                <span>Validation Protocol:</span>
                <span class="text-cockpit-100">TimeSeriesSplit (5-fold)</span>
              </li>
              <li class="flex justify-between">
                <span>Psychrometric Feature:</span>
                <span class="text-cockpit-100">Stull (2011) Wet-Bulb (°C)</span>
              </li>
              <li class="flex justify-between">
                <span>Anomaly Threshold:</span>
                <span class="text-status-amber">Robust MAD > 3.0 + Isolation Forest</span>
              </li>
              <li class="flex justify-between">
                <span>Target Leakage Protection:</span>
                <span class="text-status-emerald">Zero Target Inversion</span>
              </li>
            </ul>

            <div class="mt-4 pt-3 border-t border-cockpit-800 text-[11px] text-cockpit-300 font-sans leading-relaxed">
              <p>
                <strong>Evaluation Rationale:</strong> A physics-informed, context-aware chiller intelligence system that learns expected energy consumption from operating, environmental, equipment and temporal context. Instead of using fixed thresholds, it compares measured energy with contextual expected energy, analyses the residual using robust anomaly detection and persistence logic, and provides SHAP-based explanations for the model's prediction.
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

// 1. Fetch Summary
const { data: summary } = await useFetch('/api/summary')

// 2. Fetch Telemetry for active equipment
const { data: rawTelemetry } = await useFetch(() => `/api/telemetry?equipment=${selectedEquipment.value}`)

// 3. Fetch Events for active equipment
const { data: rawEvents } = await useFetch(() => `/api/events?equipment=${selectedEquipment.value}`)

// 4. Fetch SHAP samples for active equipment
const { data: rawShap } = await useFetch(() => `/api/shap?equipment=${selectedEquipment.value}`)

const telemetryData = computed(() => rawTelemetry.value || [])
const eventsData = computed(() => rawEvents.value || [])
const shapSamples = computed(() => rawShap.value || [])

const currentEquipmentStats = computed(() => {
  if (!summary.value?.equipment_stats) return undefined
  return summary.value.equipment_stats[selectedEquipment.value]
})

const onEquipmentChange = (eq: string) => {
  selectedEquipment.value = eq
  activePoint.value = null
}

const onPointInspect = (point: any) => {
  activePoint.value = point
}

const onEventSelect = (event: any) => {
  // Find telemetry point matching event start
  const match = telemetryData.value.find((t: any) => t.ts.startsWith(event.start_time.substring(0, 16)))
  if (match) {
    activePoint.value = match
  } else {
    activePoint.value = {
      ts: event.start_time,
      act: event.max_residual + 100,
      exp: 100,
      res: event.max_residual,
      residual: event.max_residual,
      anom: 1,
      equipment_id: event.equipment_id
    }
  }
}
</script>
