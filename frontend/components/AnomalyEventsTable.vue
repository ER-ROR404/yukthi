<template>
  <div class="card-solid bg-white border border-slate-300 rounded-xl overflow-hidden shadow-xs hover:border-slate-400 transition-colors">
    
    <!-- Table Header & Controls -->
    <div class="px-5 sm:px-6 py-4 sm:py-5 bg-slate-100 border-b border-slate-300 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
      <div>
        <div class="flex items-center space-x-2.5">
          <h3 class="text-base sm:text-xl font-bold text-slate-950 font-sans tracking-tight">
            Persistent Operational Anomaly Episodes
          </h3>
          <span class="text-xs px-2.5 py-0.5 rounded font-mono font-bold bg-white text-slate-800 border border-slate-300 shadow-xs">
            {{ filteredSortedEvents.length }} Consolidated Episodes
          </span>
        </div>
        <p class="text-xs sm:text-sm text-slate-600 mt-1 font-sans font-medium">
          Consecutive sustained deviations grouped into consolidated maintenance events (avoids noisy point alerts).
        </p>
      </div>

      <!-- Search & Filter Bar -->
      <div class="flex flex-wrap items-center gap-2.5">
        <!-- Quick Search -->
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search #, date, severity..."
            class="text-sm pl-9 pr-8 py-1.5 rounded-lg border border-slate-300 bg-white focus:outline-none focus:border-blue-600 font-sans w-52 sm:w-60 text-slate-900 transition-colors"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 p-0.5 cursor-pointer"
            title="Clear search"
          >
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Filter Tabs -->
        <div class="flex items-center bg-slate-200/80 p-1 rounded-lg border border-slate-300 text-xs sm:text-sm font-medium">
          <button
            v-for="filter in filters"
            :key="filter.id"
            @click="setFilter(filter.id)"
            :class="[
              'px-3 py-1.5 rounded-md transition-colors cursor-pointer text-xs sm:text-sm',
              activeFilter === filter.id
                ? 'bg-white text-slate-950 shadow-xs font-bold border border-slate-300'
                : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Table Body Container with clean padding -->
    <div class="p-5 sm:p-6 space-y-4">
      <!-- Interactive Event Table -->
      <div
        :class="[
          'overflow-x-auto border border-slate-300 rounded-lg transition-all bg-white',
          displayedEvents.length > 10 ? 'max-h-[580px] overflow-y-auto' : ''
        ]"
      >
      <table class="w-full text-left text-sm font-mono border-collapse">
        <thead class="sticky top-0 z-20 font-sans shadow-xs">
          <tr class="border-b-2 border-slate-300">
            <th
              @click="toggleSort('event_id')"
              class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-slate-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Event</span>
                <component :is="getSortIcon('event_id')" class="w-3.5 h-3.5 text-slate-600" />
              </div>
            </th>
            <th class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider">Unit</th>
            <th
              @click="toggleSort('start_time')"
              class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-slate-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Start Time Window</span>
                <component :is="getSortIcon('start_time')" class="w-3.5 h-3.5 text-slate-600" />
              </div>
            </th>
            <th
              @click="toggleSort('duration_minutes')"
              class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-slate-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Duration</span>
                <component :is="getSortIcon('duration_minutes')" class="w-3.5 h-3.5 text-slate-600" />
              </div>
            </th>
            <th
              @click="toggleSort('max_residual')"
              class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider text-right cursor-pointer select-none hover:text-slate-950 transition-colors"
            >
              <div class="flex items-center justify-end space-x-1">
                <span>Peak Dev</span>
                <component :is="getSortIcon('max_residual')" class="w-3.5 h-3.5 text-slate-600" />
              </div>
            </th>
            <th class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider text-right">Mean Dev</th>
            <th class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider text-center">Severity</th>
            <th class="table-header-cell py-3.5 px-4 font-bold text-slate-800 uppercase text-xs tracking-wider text-right">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-200 text-slate-800">
          <tr
            v-for="ev in displayedEvents"
            :key="ev.event_id"
            @click="$emit('select-event', ev)"
            :class="[
              'transition-colors cursor-pointer text-sm',
              selectedEventId === ev.event_id
                ? 'bg-blue-50/90 font-medium border-l-4 border-blue-600'
                : 'hover:bg-slate-50'
            ]"
          >
            <td class="py-3 px-4 font-bold text-slate-950">#{{ String(ev.event_id).padStart(3, '0') }}</td>
            <td class="py-3 px-4 text-slate-800 font-semibold">{{ ev.equipment_id }}</td>
            <td class="py-3 px-4 text-slate-700 font-sans text-sm font-medium">
              {{ ev.start_time.replace('T', ' ').substring(0, 16) }}
            </td>
            <td class="py-3 px-4 text-slate-800 font-medium">
              {{ formatDuration(ev.duration_minutes) }}
            </td>
            <td class="py-3 px-4 text-right font-bold text-sm sm:text-base" :class="ev.max_residual > 30 ? 'text-red-700' : 'text-orange-700'">
              +{{ ev.max_residual.toFixed(1) }} kWh
            </td>
            <td class="py-3 px-4 text-right text-slate-700 font-medium">
              +{{ ev.mean_residual.toFixed(1) }} kWh
            </td>
            <td class="py-3 px-4 text-center">
              <span
                :class="[
                  'px-2.5 py-1 rounded text-xs font-bold tracking-wide uppercase',
                  getSeverity(ev).badgeClass
                ]"
              >
                {{ getSeverity(ev).label }}
              </span>
            </td>
            <td class="py-3 px-4 text-right">
              <button
                class="px-3.5 py-1.5 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold border border-blue-200 transition-colors cursor-pointer"
                @click.stop="$emit('select-event', ev)"
              >
                Inspect
              </button>
            </td>
          </tr>

          <tr v-if="displayedEvents.length === 0">
            <td colspan="8" class="py-12 text-center text-slate-500 font-sans text-sm">
              <div class="space-y-2">
                <p class="font-medium">No anomaly events match the selected criteria.</p>
                <button
                  v-if="searchQuery || activeFilter !== 'ALL'"
                  @click="resetFilters"
                  class="text-sm font-semibold text-blue-600 hover:underline cursor-pointer"
                >
                  Reset filters & search
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Table Footer: Progressive Disclosure ('See More') -->
    <div class="mt-4 pt-3.5 border-t border-slate-200">
      
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-100 p-3.5 rounded-lg border border-slate-300">
        
        <!-- Status Indicator -->
        <div class="flex items-center space-x-3 text-sm font-sans font-medium">
          <span class="text-slate-700">
            Showing
            <strong class="font-mono text-slate-950 font-bold">{{ displayedRangeText }}</strong>
            of
            <strong class="font-mono text-slate-950 font-bold">{{ filteredSortedEvents.length }}</strong>
            episodes
          </span>
          
          <span
            v-if="remainingCount > 0"
            class="text-xs font-mono text-slate-800 bg-slate-200 border border-slate-300 px-2.5 py-0.5 rounded font-semibold"
          >
            {{ remainingCount }} remaining
          </span>
          <span
            v-else-if="filteredSortedEvents.length > 0"
            class="text-xs font-mono text-emerald-900 bg-emerald-100 border border-emerald-300 px-2.5 py-0.5 rounded font-bold"
          >
            All Loaded
          </span>
        </div>

        <!-- Interactive Progressive Disclosure Controls -->
        <div class="flex flex-wrap items-center gap-2.5">
          
          <!-- See More Button (appends next 10 episodes in place) -->
          <button
            v-if="remainingCount > 0"
            @click="loadMore"
            class="flex items-center space-x-1.5 px-4 py-2 bg-white hover:bg-slate-50 text-slate-950 font-bold text-sm rounded-md border border-slate-300 shadow-xs transition-colors cursor-pointer"
          >
            <span>See More (+{{ Math.min(10, remainingCount) }})</span>
            <ChevronDown class="w-4 h-4 text-slate-700" />
          </button>

          <!-- See All Button -->
          <button
            v-if="remainingCount > 0"
            @click="showAll"
            class="px-3 py-2 text-sm font-bold text-blue-700 hover:text-blue-900 hover:underline cursor-pointer"
          >
            See All ({{ filteredSortedEvents.length }})
          </button>

          <!-- Collapse Button (when expanded beyond initial 10) -->
          <button
            v-if="progressiveVisibleCount > 10"
            @click="collapseToInitial"
            class="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-200 hover:bg-slate-300 text-slate-900 font-bold text-sm rounded-md border border-slate-300 transition-colors cursor-pointer"
          >
            <span>Collapse</span>
            <ChevronUp class="w-4 h-4 text-slate-700" />
          </button>

        </div>

      </div>

    </div>

  </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  ChevronDown,
  ChevronUp,
  Search,
  X,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from 'lucide-vue-next'

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

// Filter & Search State
const activeFilter = ref('ALL')
const searchQuery = ref('')

const filters = [
  { id: 'ALL', label: 'All Episodes' },
  { id: 'HIGH', label: 'High Severity' },
  { id: 'SUSTAINED', label: 'Sustained (>2h)' },
  { id: 'CRITICAL', label: 'Peak Dev > 30 kWh' }
]

// Sorting State
const sortKey = ref<'event_id' | 'start_time' | 'duration_minutes' | 'max_residual'>('event_id')
const sortOrder = ref<'asc' | 'desc'>('asc')

const toggleSort = (key: 'event_id' | 'start_time' | 'duration_minutes' | 'max_residual') => {
  if (sortKey.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortOrder.value = key === 'max_residual' || key === 'duration_minutes' ? 'desc' : 'asc'
  }
}

const getSortIcon = (key: string) => {
  if (sortKey.value !== key) return ArrowUpDown
  return sortOrder.value === 'asc' ? ArrowUp : ArrowDown
}

// Progressive Disclosure ("See More") State - No split batch
const progressiveVisibleCount = ref(10)

const setFilter = (id: string) => {
  activeFilter.value = id
  resetProgressive()
}

const resetFilters = () => {
  activeFilter.value = 'ALL'
  searchQuery.value = ''
  resetProgressive()
}

const resetProgressive = () => {
  progressiveVisibleCount.value = 10
}

// Formatters
const getSeverity = (ev: any) => {
  if (ev.max_residual > 30 || ev.duration_minutes >= 180) {
    return {
      label: 'High',
      badgeClass: 'bg-red-100 text-red-900 border border-red-300 font-bold'
    }
  }
  if (ev.max_residual > 15 || ev.duration_minutes >= 60) {
    return {
      label: 'Medium',
      badgeClass: 'bg-amber-100 text-amber-900 border border-amber-300 font-bold'
    }
  }
  return {
    label: 'Low',
    badgeClass: 'bg-slate-200 text-slate-800 border border-slate-300 font-bold'
  }
}

const formatDuration = (mins: number) => {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

// Computed: Filtered + Searched + Sorted Events
const filteredSortedEvents = computed(() => {
  let list = props.events || []

  // 1. Filter Tab
  if (activeFilter.value === 'HIGH') {
    list = list.filter((e) => e.max_residual > 30 || e.duration_minutes >= 180)
  } else if (activeFilter.value === 'SUSTAINED') {
    list = list.filter((e) => e.duration_minutes >= 120)
  } else if (activeFilter.value === 'CRITICAL') {
    list = list.filter((e) => e.max_residual > 30)
  }

  // 2. Search Query
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter((e) => {
      const idMatch = String(e.event_id).includes(q) || `#${String(e.event_id).padStart(3, '0')}`.toLowerCase().includes(q)
      const unitMatch = (e.equipment_id || '').toLowerCase().includes(q)
      const timeMatch = (e.start_time || '').toLowerCase().includes(q)
      const severityMatch = getSeverity(e).label.toLowerCase().includes(q)
      return idMatch || unitMatch || timeMatch || severityMatch
    })
  }

  // 3. Sorting
  const sorted = [...list]
  sorted.sort((a, b) => {
    let valA = a[sortKey.value]
    let valB = b[sortKey.value]

    if (sortKey.value === 'start_time') {
      valA = new Date(valA).getTime()
      valB = new Date(valB).getTime()
    }

    if (valA < valB) return sortOrder.value === 'asc' ? -1 : 1
    if (valA > valB) return sortOrder.value === 'asc' ? 1 : -1
    return 0
  })

  return sorted
})

// Computed: Final Displayed Events (progressive 'See More' slice)
const displayedEvents = computed(() => {
  const total = filteredSortedEvents.value.length
  if (total === 0) return []
  return filteredSortedEvents.value.slice(0, progressiveVisibleCount.value)
})

// Remaining items count
const remainingCount = computed(() => {
  return Math.max(0, filteredSortedEvents.value.length - progressiveVisibleCount.value)
})

// Range text (e.g. "1–10" or "1–30")
const displayedRangeText = computed(() => {
  const count = displayedEvents.value.length
  if (count === 0) return '0'
  return `1–${count}`
})

// User Actions
const loadMore = () => {
  progressiveVisibleCount.value = Math.min(
    filteredSortedEvents.value.length,
    progressiveVisibleCount.value + 10
  )
}

const showAll = () => {
  progressiveVisibleCount.value = filteredSortedEvents.value.length
}

const collapseToInitial = () => {
  progressiveVisibleCount.value = 10
}

// Watchers: Keep selection in view when selectedEventId changes
watch(
  () => props.selectedEventId,
  (newId) => {
    if (newId === undefined || newId === null) return
    const idx = filteredSortedEvents.value.findIndex((e) => e.event_id === newId)
    if (idx >= 0 && progressiveVisibleCount.value <= idx) {
      progressiveVisibleCount.value = Math.ceil((idx + 1) / 10) * 10
    }
  }
)

// Reset when raw equipment events prop changes
watch(
  () => props.events,
  () => {
    resetProgressive()
  }
)
</script>

<style scoped>
thead th,
.table-header-cell {
  background-color: #e2e8f0 !important;
  opacity: 1 !important;
  color: #0f172a !important;
}
</style>
