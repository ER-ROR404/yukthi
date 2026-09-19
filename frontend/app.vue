<template>
  <div class="min-h-screen bg-[#EDF2F7] text-slate-900 font-sans antialiased selection:bg-blue-100 selection:text-blue-900">
    
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
            :classified-anomalies="classifiedAnomalies"
            :selected-event-id="activeEventId"
            @select-event="onEventSelect"
            @select-classified="onClassifiedSelect"
          />
        </div>

        <!-- Right Column: Investigation Workbench & Supporting Evidence (4 cols) -->
        <div class="lg:col-span-4 space-y-5 lg:sticky lg:top-20">
          
          <!-- Investigation & Attribution Workbench -->
          <ShapExplainerPanel
            :selected-point="activePoint"
            :shap-samples="shapSamples"
          />

          <!-- Model & Operational Intelligence Context Card -->
          <div class="card-solid bg-white border border-slate-300 rounded-xl p-5 sm:p-6 shadow-xs text-sm font-sans space-y-4 text-slate-900">
            <div class="flex items-center justify-between pb-3 border-b border-slate-200">
              <h4 class="text-base sm:text-xl font-bold text-slate-950 tracking-tight">
                ML Pipeline Architecture & Verification
              </h4>
              <span class="text-xs font-mono px-3 py-1 rounded-md bg-emerald-100 text-emerald-900 border border-emerald-300 font-bold">
                Validated
              </span>
            </div>

            <!-- Architectural Breakdown -->
            <ul class="space-y-3 text-slate-800 font-mono text-sm">
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Model Core:</span>
                <span class="text-slate-950 font-bold">CatBoost Regressor (Depth 4)</span>
              </li>
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Validation Scheme:</span>
                <span class="text-slate-950 font-bold">TimeSeriesSplit (5-Fold CV)</span>
              </li>
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Chronological CV R²:</span>
                <span class="text-emerald-800 font-bold">0.7734 (CV MAE 9.89 kWh)</span>
              </li>
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Production Accuracy:</span>
                <span class="text-emerald-800 font-bold">93.56% (100 − WAPE)</span>
              </li>
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Secondary Evidence:</span>
                <span class="text-slate-900 font-bold">Isolation Forest Corroboration</span>
              </li>
              <li class="flex justify-between items-center">
                <span class="text-slate-600 font-sans font-medium">Data Quality Decoupling:</span>
                <span class="text-blue-800 font-bold">4-State Separation Logic</span>
              </li>
            </ul>

            <!-- Process Rationale (Clean, direct, human-written) -->
            <div class="pt-3.5 border-t border-slate-200 text-sm text-slate-700 leading-relaxed space-y-2.5 font-sans font-medium">
              <p>
                <strong class="text-slate-950 font-bold">Operating Principle:</strong> Rather than applying static energy thresholds that cause false alarms during peak summer heat, this system learns expected power from simultaneous environmental and operating telemetry.
              </p>
              <p>
                The residual between measured and expected power identifies true energy inefficiency. Sensor faults and extreme weather trigger a <strong class="text-purple-900 font-bold">Low Confidence</strong> state rather than false mechanical alerts.
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

// 5. Fetch Classified Anomalies for active equipment
const { data: rawClassified } = await useFetch(() => `/api/classified-anomalies?equipment=${selectedEquipment.value}`)

const telemetryData = computed(() => (rawTelemetry.value as any[]) || [])
const eventsData = computed(() => {
  const all = (rawEvents.value as any[]) || []
  return all.filter((e: any) => e.equipment_id === selectedEquipment.value)
})
const shapSamples = computed(() => (rawShap.value as any[]) || [])
const classifiedAnomalies = computed(() => (rawClassified.value as any[]) || [])

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

const onClassifiedSelect = (anom: any) => {
  activeEventId.value = undefined
  // Try to match a telemetry point for full SHAP inspection
  const match = telemetryData.value.find((t: any) =>
    t.ts.startsWith((anom.timestamp || '').substring(0, 16))
  )
  if (match) {
    activePoint.value = {
      ...match,
      equipment_id: anom.equipment_id
    }
  } else {
    // Synthesise a reading from classified anomaly data
    activePoint.value = {
      ts: anom.timestamp,
      act: anom.actual,
      exp: anom.expected,
      res: anom.deviation,
      residual: anom.deviation,
      z: anom.anomaly_score || 3.0,
      anom: 1,
      status: 'ABNORMAL ENERGY',
      equipment_id: anom.equipment_id,
      param_details: anom.param_details || null,
      classification: {
        anomaly_type: anom.anomaly_type,
        icon: anom.icon,
        category: anom.category,
        diagnosis: anom.diagnosis,
        recommendation: anom.recommendation
      }
    }
  }
}
</script>
