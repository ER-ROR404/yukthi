<template>
  <div class="bg-cockpit-900 border border-cockpit-800 rounded-lg p-4">
    <div class="flex items-center justify-between pb-3 border-b border-cockpit-800/60 mb-3">
      <div>
        <h3 class="text-sm font-semibold text-cockpit-100 flex items-center space-x-2">
          <span>Persistent Anomaly Event Clusters</span>
        </h3>
        <p class="text-xs text-cockpit-300">
          Consecutive sustained deviations grouped into consolidated maintenance event logs.
        </p>
      </div>
      <span class="text-xs font-mono text-cockpit-300">
        {{ events.length }} events logged
      </span>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto max-h-72 overflow-y-auto border border-cockpit-800 rounded">
      <table class="w-full text-left text-xs font-mono">
        <thead class="bg-cockpit-950 text-cockpit-300 uppercase text-[10px] tracking-wider sticky top-0 border-b border-cockpit-800">
          <tr>
            <th class="py-2 px-3">Event ID</th>
            <th class="py-2 px-3">Unit</th>
            <th class="py-2 px-3">Start Window</th>
            <th class="py-2 px-3">Duration</th>
            <th class="py-2 px-3 text-right">Max Dev</th>
            <th class="py-2 px-3 text-right">Mean Dev</th>
            <th class="py-2 px-3 text-center">Obs</th>
            <th class="py-2 px-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-cockpit-800/60 text-cockpit-100">
          <tr
            v-for="ev in events.slice(0, 50)"
            :key="ev.event_id"
            class="hover:bg-cockpit-800/50 transition-colors cursor-pointer"
            @click="$emit('select-event', ev)"
          >
            <td class="py-2 px-3 font-semibold text-cockpit-100">#{{ ev.event_id }}</td>
            <td class="py-2 px-3 text-cockpit-300">{{ ev.equipment_id }}</td>
            <td class="py-2 px-3 text-cockpit-300">{{ ev.start_time.replace('T', ' ').substring(0, 16) }}</td>
            <td class="py-2 px-3 text-cockpit-300">{{ ev.duration_minutes }}m</td>
            <td class="py-2 px-3 text-right font-bold text-status-amber">+{{ ev.max_residual }} kWh</td>
            <td class="py-2 px-3 text-right text-cockpit-300">+{{ ev.mean_residual }} kWh</td>
            <td class="py-2 px-3 text-center">
              <span class="px-1.5 py-0.5 rounded bg-cockpit-800 text-cockpit-300 text-[10px]">
                {{ ev.observation_count }}
              </span>
            </td>
            <td class="py-2 px-3 text-right">
              <button
                class="px-2 py-1 rounded bg-status-blue/10 text-status-blue hover:bg-status-blue/20 text-[10px] font-semibold transition-colors"
                @click.stop="$emit('select-event', ev)"
              >
                Inspect
              </button>
            </td>
          </tr>
          <tr v-if="events.length === 0">
            <td colspan="8" class="py-6 text-center text-cockpit-300">
              No persistent anomaly events detected in this slice.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
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
}>()

defineEmits<{
  (e: 'select-event', event: any): void
}>()
</script>
