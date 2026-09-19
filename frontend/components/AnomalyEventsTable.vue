<template>
  <div class="bg-white border border-surface-200 rounded-xl p-5 sm:p-6 shadow-card">
    
    <!-- Table Header & Filter Tabs -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 mb-3.5 border-b border-surface-200">
      <div>
        <h3 class="text-base sm:text-lg font-bold text-surface-900 font-sans tracking-tight flex items-center space-x-2.5">
          <span>Persistent Operational Anomaly Episodes</span>
          <span class="text-xs px-2.5 py-0.5 rounded font-mono font-medium bg-surface-100 text-surface-700 border border-surface-200">
            {{ filteredEvents.length }} Consolidated Episodes
          </span>
        </h3>
        <p class="text-xs sm:text-sm text-surface-600 mt-0.5 font-sans">
          Consecutive sustained deviations grouped into consolidated maintenance events (avoids noisy point alerts).
        </p>
      </div>

      <!-- Filter Tabs -->
      <div class="flex items-center bg-surface-100 p-1 rounded-lg border border-surface-200 text-xs sm:text-sm font-medium">
        <button
          v-for="filter in filters"
          :key="filter.id"
          @click="activeFilter = filter.id"
          :class="[
            'px-3 py-1.5 rounded-md transition-colors cursor-pointer',
            activeFilter === filter.id
              ? 'bg-white text-surface-900 shadow-xs font-bold'
              : 'text-surface-600 hover:text-surface-900'
          ]"
        >
          {{ filter.label }}
        </button>
      </div>
    </div>

    <!-- Interactive Event Table -->
    <div class="overflow-x-auto max-h-84 overflow-y-auto border border-surface-200 rounded-lg">
      <table class="w-full text-left text-xs sm:text-sm font-mono">
        <thead class="bg-surface-50 text-surface-600 uppercase text-xs tracking-wider sticky top-0 border-b border-surface-200 z-10 font-sans">
          <tr>
            <th class="py-3 px-3.5 font-semibold">Event</th>
            <th class="py-3 px-3.5 font-semibold">Unit</th>
            <th class="py-3 px-3.5 font-semibold">Start Time Window</th>
            <th class="py-3 px-3.5 font-semibold">Duration</th>
            <th class="py-3 px-3.5 font-semibold text-right">Peak Deviation</th>
            <th class="py-3 px-3.5 font-semibold text-right">Mean Deviation</th>
            <th class="py-3 px-3.5 font-semibold text-center">Severity</th>
            <th class="py-3 px-3.5 font-semibold text-right">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100 text-surface-800">
          <tr
            v-for="ev in filteredEvents.slice(0, 50)"
            :key="ev.event_id"
            @click="$emit('select-event', ev)"
            :class="[
              'transition-colors cursor-pointer text-xs sm:text-sm',
              selectedEventId === ev.event_id
                ? 'bg-brand-50/70 font-medium'
                : 'hover:bg-surface-50'
            ]"
          >
            <td class="py-3 px-3.5 font-bold text-surface-900">#{{ String(ev.event_id).padStart(3, '0') }}</td>
            <td class="py-3 px-3.5 text-surface-700 font-medium">{{ ev.equipment_id }}</td>
            <td class="py-3 px-3.5 text-surface-700 font-sans text-xs sm:text-sm">
              {{ ev.start_time.replace('T', ' ').substring(0, 16) }}
            </td>
            <td class="py-3 px-3.5 text-surface-700">
              {{ formatDuration(ev.duration_minutes) }}
            </td>
            <td class="py-3 px-3.5 text-right font-bold text-sm sm:text-base" :class="ev.max_residual > 30 ? 'text-red-700' : 'text-orange-700'">
              +{{ ev.max_residual.toFixed(1) }} kWh
            </td>
            <td class="py-3 px-3.5 text-right text-surface-600 font-medium">
              +{{ ev.mean_residual.toFixed(1) }} kWh
            </td>
            <td class="py-3 px-3.5 text-center">
              <span
                :class="[
                  'px-2.5 py-1 rounded text-xs font-semibold tracking-wide uppercase',
                  getSeverity(ev).badgeClass
                ]"
              >
                {{ getSeverity(ev).label }}
              </span>
            </td>
            <td class="py-3 px-3.5 text-right">
              <button
                class="px-3 py-1.5 rounded-md bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-bold border border-brand-200/80 transition-colors cursor-pointer"
                @click.stop="$emit('select-event', ev)"
              >
                Inspect
              </button>
            </td>
          </tr>

          <tr v-if="filteredEvents.length === 0">
            <td colspan="8" class="py-10 text-center text-surface-500 font-sans text-sm">
              No anomaly events match the selected filter.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Table Footer Note -->
    <div class="mt-3 flex items-center justify-between text-xs text-surface-500 font-sans">
      <span>Showing top 50 chronological episodes. Click any row to focus investigation.</span>
      <span class="font-mono text-surface-600 font-medium">Trigger: Robust MAD > 3.0 on 7-day baseline</span>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  events: Array<{
    event_id: number
    equipment_id: string
    start_time: string
    end_time: string
    duration_minutes: number
    max_residual: number
    mean_residual: number
    max_z_score: number
    observation_count: number
  }>
  selectedEventId?: number
}>()

defineEmits<{
  (e: 'select-event', event: any): void
}>()

const activeFilter = ref('ALL')

const filters = [
  { id: 'ALL', label: 'All Episodes' },
  { id: 'HIGH', label: 'High Severity' },
  { id: 'SUSTAINED', label: 'Sustained (>2h)' },
  { id: 'CRITICAL', label: 'Peak Dev > 30 kWh' }
]

const getSeverity = (ev: any) => {
  if (ev.max_residual > 30 || ev.duration_minutes >= 180) {
    return {
      label: 'High',
      badgeClass: 'bg-red-50 text-red-800 border border-red-200'
    }
  }
  if (ev.max_residual > 15 || ev.duration_minutes >= 60) {
    return {
      label: 'Medium',
      badgeClass: 'bg-amber-50 text-amber-800 border border-amber-200'
    }
  }
  return {
    label: 'Low',
    badgeClass: 'bg-surface-100 text-surface-700 border border-surface-200'
  }
}

const formatDuration = (mins: number) => {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

const filteredEvents = computed(() => {
  if (activeFilter.value === 'HIGH') {
    return props.events.filter((e) => e.max_residual > 30 || e.duration_minutes >= 180)
  }
  if (activeFilter.value === 'SUSTAINED') {
    return props.events.filter((e) => e.duration_minutes >= 120)
  }
  if (activeFilter.value === 'CRITICAL') {
    return props.events.filter((e) => e.max_residual > 30)
  }
  return props.events
})
</script>
