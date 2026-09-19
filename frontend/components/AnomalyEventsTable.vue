<template>
  <div class="card-solid bg-white border border-slate-300 rounded-xl overflow-hidden shadow-xs hover:border-slate-400 transition-colors">
    
    <!-- Header: Modern Cockpit Control Bar -->
    <div class="px-5 sm:px-6 py-4 sm:py-5 bg-slate-100 border-b border-slate-300 space-y-3.5">
      
      <!-- Top Row: Title + View Mode Pill Switcher -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div class="flex items-center space-x-2.5">
            <h3 class="text-base sm:text-xl font-bold text-slate-950 font-sans tracking-tight">
              Operational Anomaly Intelligence
            </h3>
            <span class="text-xs px-2.5 py-0.5 rounded font-mono font-bold bg-white text-slate-800 border border-slate-300 shadow-xs">
              {{ currentTableCount }} Detected
            </span>
          </div>
          <p class="text-xs sm:text-sm text-slate-600 mt-1 font-sans font-medium">
            Multi-sensor operational deviations: power surges, meter drops, cooling tower overheating, and pumping waste.
          </p>
        </div>

        <!-- View Mode Switcher -->
        <div class="inline-flex p-1 bg-slate-200/80 rounded-lg border border-slate-300 self-start sm:self-auto text-xs font-sans font-semibold">
          <button
            @click="activeViewMode = 'classified'"
            :class="[
              'px-3.5 py-1.5 rounded-md transition-all cursor-pointer flex items-center space-x-1.5',
              activeViewMode === 'classified'
                ? 'bg-white text-slate-950 shadow-xs font-bold border border-slate-300'
                : 'text-slate-700 hover:text-slate-950'
            ]"
          >
            <span>⚡ Anomaly Categories</span>
            <span class="text-[11px] px-1.5 py-0.2 rounded bg-blue-100 text-blue-900 font-mono font-bold">
              {{ filteredClassified.length }}
            </span>
          </button>

          <button
            @click="activeViewMode = 'episodes'"
            :class="[
              'px-3.5 py-1.5 rounded-md transition-all cursor-pointer flex items-center space-x-1.5',
              activeViewMode === 'episodes'
                ? 'bg-white text-slate-950 shadow-xs font-bold border border-slate-300'
                : 'text-slate-700 hover:text-slate-950'
            ]"
          >
            <span>🗂️ Consolidated Episodes</span>
            <span class="text-[11px] px-1.5 py-0.2 rounded bg-slate-200 text-slate-800 font-mono font-bold">
              {{ filteredSortedEvents.length }}
            </span>
          </button>
        </div>
      </div>

      <!-- Second Row: Category Filters + Search -->
      <div class="flex flex-wrap items-center justify-between gap-2.5 pt-1">
        
        <!-- Category Filter Pills (When in Classified View) -->
        <div v-if="activeViewMode === 'classified'" class="flex flex-wrap items-center gap-1.5 text-xs font-medium font-sans">
          <button
            v-for="cat in categoryFilters"
            :key="cat.id"
            @click="activeCategory = cat.id; resetProgressive()"
            :class="[
              'px-3 py-1.5 rounded-md transition-colors cursor-pointer flex items-center space-x-1.5 border',
              activeCategory === cat.id
                ? 'bg-white text-slate-950 font-bold border-slate-400 shadow-xs'
                : 'bg-slate-200/60 text-slate-700 border-transparent hover:bg-slate-200'
            ]"
          >
            <span>{{ cat.label }}</span>
            <span v-if="cat.count !== undefined" class="text-[10px] font-mono font-bold text-slate-500">
              ({{ cat.count }})
            </span>
          </button>
        </div>

        <!-- Severity Filters (When in Episodes View) -->
        <div v-else class="flex items-center bg-slate-200/80 p-1 rounded-lg border border-slate-300 text-xs font-medium font-sans">
          <button
            v-for="filter in episodeFilters"
            :key="filter.id"
            @click="activeEpisodeFilter = filter.id; resetProgressive()"
            :class="[
              'px-3 py-1.5 rounded-md transition-colors cursor-pointer text-xs',
              activeEpisodeFilter === filter.id
                ? 'bg-white text-slate-950 shadow-xs font-bold border border-slate-300'
                : 'text-slate-700 hover:text-slate-950'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>

        <!-- Quick Search Bar -->
        <div class="relative">
          <Search class="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search anomaly, date, value..."
            class="text-xs sm:text-sm pl-9 pr-8 py-1.5 rounded-lg border border-slate-300 bg-white focus:outline-none focus:border-blue-600 font-sans w-52 sm:w-64 text-slate-900 transition-colors"
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

      </div>

    </div>

    <!-- Table Body -->
    <div class="p-5 sm:p-6 space-y-4">

      <!-- ========================================================== -->
      <!-- VIEW 1: CATEGORIZED MULTI-TYPE ANOMALIES TABLE             -->
      <!-- ========================================================== -->
      <div
        v-if="activeViewMode === 'classified'"
        :class="[
          'overflow-x-auto border border-slate-300 rounded-lg transition-all bg-white',
          displayedClassified.length > 10 ? 'max-h-[580px] overflow-y-auto' : ''
        ]"
      >
        <table class="w-full text-left text-sm font-mono border-collapse">
          <thead class="sticky top-0 z-20 font-sans shadow-xs bg-slate-200">
            <tr class="border-b-2 border-slate-300 text-slate-900">
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider">Unit & Time</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider">Anomaly Type</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider">Parameter</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider text-right">Deviation Value</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider text-center">Anomaly Score</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider">Plain-English Diagnosis</th>
              <th class="table-header-cell py-3 px-4 font-bold uppercase text-xs tracking-wider text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-200 text-slate-800">
            <tr
              v-for="(anom, idx) in displayedClassified"
              :key="`${anom.equipment_id}-${anom.timestamp}-${idx}`"
              @click="$emit('select-classified', anom)"
              class="hover:bg-slate-50 transition-colors cursor-pointer text-sm"
            >
              <!-- Unit & Timestamp -->
              <td class="py-3 px-4">
                <div class="font-bold text-slate-950">{{ anom.equipment_id }}</div>
                <div class="text-xs text-slate-500 font-sans mt-0.5">
                  {{ anom.timestamp.substring(0, 16).replace('T', ' ') }}
                </div>
              </td>

              <!-- Anomaly Type with Icon -->
              <td class="py-3 px-4 font-sans">
                <span
                  :class="[
                    'inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-xs font-bold shadow-2xs border',
                    getCategoryBadgeClass(anom.category)
                  ]"
                >
                  <span>{{ anom.icon }}</span>
                  <span>{{ anom.anomaly_type }}</span>
                </span>
              </td>

              <!-- Parameter Name -->
              <td class="py-3 px-4 font-sans font-medium text-slate-900">
                {{ anom.parameter }}
              </td>

              <!-- Numerical Deviation Value (Actual - Expected) -->
              <td class="py-3 px-4 text-right font-bold font-mono text-sm sm:text-base" :class="getDeviationColor(anom)">
                {{ anom.deviation > 0 ? '+' : '' }}{{ anom.deviation }} {{ anom.unit }}
                <span class="block text-[11px] font-normal text-slate-500 font-sans">
                  act: {{ anom.actual }} • exp: {{ anom.expected }}
                </span>
              </td>

              <!-- Statistical Anomaly Score (z-score) -->
              <td class="py-3 px-4 text-center">
                <div class="inline-flex items-center space-x-1">
                  <span
                    :class="[
                      'font-bold font-mono px-2.5 py-0.5 rounded text-xs',
                      anom.anomaly_score >= 4.0
                        ? 'bg-red-100 text-red-900 border border-red-300'
                        : anom.anomaly_score >= 3.0
                          ? 'bg-amber-100 text-amber-900 border border-amber-300'
                          : 'bg-slate-100 text-slate-800 border border-slate-300'
                    ]"
                  >
                    z = {{ anom.anomaly_score.toFixed(2) }}
                  </span>
                </div>
              </td>

              <!-- Plain-English Diagnosis -->
              <td class="py-3 px-4 font-sans text-xs text-slate-700 max-w-[280px] leading-relaxed">
                {{ anom.diagnosis }}
              </td>

              <!-- Action Button -->
              <td class="py-3 px-4 text-right">
                <button
                  class="px-3 py-1.5 rounded-md bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-bold border border-blue-200 transition-colors cursor-pointer"
                  @click.stop="$emit('select-classified', anom)"
                >
                  Inspect
                </button>
              </td>
            </tr>

            <tr v-if="displayedClassified.length === 0">
              <td colspan="7" class="py-12 text-center text-slate-500 font-sans">
                No matching anomalies found for the selected category or search query.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ========================================================== -->
      <!-- VIEW 2: CONSOLIDATED EPISODES TABLE (GROUPED MAINTENANCE)  -->
      <!-- ========================================================== -->
      <div
        v-else
        :class="[
          'overflow-x-auto border border-slate-300 rounded-lg transition-all bg-white',
          displayedEvents.length > 10 ? 'max-h-[580px] overflow-y-auto' : ''
        ]"
      >
        <table class="w-full text-left text-sm font-mono border-collapse">
          <thead class="sticky top-0 z-20 font-sans shadow-xs bg-slate-200">
            <tr class="border-b-2 border-slate-300 text-slate-900">
              <th @click="toggleSort('event_id')" class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider cursor-pointer">
                Event
              </th>
              <th class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider">Unit</th>
              <th @click="toggleSort('start_time')" class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider cursor-pointer">
                Time Window
              </th>
              <th @click="toggleSort('duration_minutes')" class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider cursor-pointer">
                Duration
              </th>
              <th class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider">Primary Anomaly</th>
              <th @click="toggleSort('max_residual')" class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider text-right cursor-pointer">
                Peak Dev
              </th>
              <th class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider text-center">Score</th>
              <th class="table-header-cell py-3.5 px-4 font-bold uppercase text-xs tracking-wider text-right">Action</th>
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
              <td class="py-3 px-4 font-sans text-xs font-semibold text-slate-900">
                <span class="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded bg-slate-100 border border-slate-300">
                  <span>{{ ev.anomaly_icon || '⚡' }}</span>
                  <span>{{ ev.anomaly_type || 'Excess Power Surge' }}</span>
                </span>
              </td>
              <td class="py-3 px-4 text-right font-bold text-sm sm:text-base" :class="ev.max_residual > 30 ? 'text-red-700' : 'text-orange-700'">
                +{{ ev.max_residual.toFixed(1) }} kWh
              </td>
              <td class="py-3 px-4 text-center font-mono font-bold text-xs text-slate-800">
                z = {{ (ev.max_z_score || 3.2).toFixed(2) }}
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
              <td colspan="8" class="py-12 text-center text-slate-500 font-sans">
                No matching episodes found.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Progressive Disclosure Footer (See More / Collapse) -->
      <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pt-2 text-xs sm:text-sm font-sans">
        <div class="text-slate-600 font-medium">
          Showing <span class="font-bold text-slate-900 font-mono">{{ displayedCountText }}</span> of <span class="font-bold text-slate-900 font-mono">{{ totalActiveListCount }}</span> records
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="hasRemaining"
            @click="loadMore"
            class="flex items-center space-x-1.5 px-4 py-2 bg-white hover:bg-slate-50 text-slate-950 font-bold text-xs sm:text-sm rounded-md border border-slate-300 shadow-xs transition-colors cursor-pointer"
          >
            <span>See More (+15)</span>
            <ChevronDown class="w-4 h-4 text-slate-700" />
          </button>

          <button
            v-if="progressiveVisibleCount > 15"
            @click="collapseToInitial"
            class="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-200 hover:bg-slate-300 text-slate-900 font-bold text-xs sm:text-sm rounded-md border border-slate-300 transition-colors cursor-pointer"
          >
            <span>Collapse</span>
            <ChevronUp class="w-4 h-4 text-slate-700" />
          </button>
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
  events: Array<any>
  selectedEventId?: number
  classifiedAnomalies?: Array<any>
}>()

const emit = defineEmits<{
  (e: 'select-event', event: any): void
  (e: 'select-classified', anom: any): void
}>()

// Active View Mode: 'classified' (default) or 'episodes'
const activeViewMode = ref<'classified' | 'episodes'>('classified')

// Category Filters for Classified View
const activeCategory = ref('ALL')
const searchQuery = ref('')
const progressiveVisibleCount = ref(15)

// Episode Filters
const activeEpisodeFilter = ref('ALL')
const episodeFilters = [
  { id: 'ALL', label: 'All Episodes' },
  { id: 'HIGH', label: 'High Severity' },
  { id: 'SUSTAINED', label: 'Sustained (>2h)' },
  { id: 'CRITICAL', label: 'Peak Dev > 30 kWh' }
]

// Sorting State for Episodes
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

// Category filter definitions with dynamic counts
const categoryFilters = computed(() => {
  const all = props.classifiedAnomalies || []
  return [
    { id: 'ALL', label: 'All Anomalies', count: all.length },
    { id: 'power_surge', label: '⚡ Power Surges', count: all.filter((a) => a.category === 'power_surge').length },
    { id: 'power_drop', label: '📉 Power Drops', count: all.filter((a) => a.category === 'power_drop').length },
    { id: 'condenser', label: '🌡️ Overheating', count: all.filter((a) => a.category === 'condenser').length },
    { id: 'pumping', label: '🌊 Pumping Waste', count: all.filter((a) => a.category === 'pumping').length },
    { id: 'load_surge', label: '🏢 Demand Surges', count: all.filter((a) => a.category === 'load_surge').length }
  ]
})

// Filtered Classified Anomalies
const filteredClassified = computed(() => {
  let list = props.classifiedAnomalies || []

  // Filter by category
  if (activeCategory.value !== 'ALL') {
    list = list.filter((a) => a.category === activeCategory.value)
  }

  // Filter by search query
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter((a) => {
      const typeMatch = (a.anomaly_type || '').toLowerCase().includes(q)
      const paramMatch = (a.parameter || '').toLowerCase().includes(q)
      const timeMatch = (a.timestamp || '').toLowerCase().includes(q)
      const diagMatch = (a.diagnosis || '').toLowerCase().includes(q)
      const eqMatch = (a.equipment_id || '').toLowerCase().includes(q)
      return typeMatch || paramMatch || timeMatch || diagMatch || eqMatch
    })
  }

  return list
})

// Displayed Classified Slice
const displayedClassified = computed(() => {
  return filteredClassified.value.slice(0, progressiveVisibleCount.value)
})

// Filtered + Sorted Episodes
const filteredSortedEvents = computed(() => {
  let list = props.events || []

  if (activeEpisodeFilter.value === 'HIGH') {
    list = list.filter((e) => e.max_residual > 30 || e.duration_minutes >= 180)
  } else if (activeEpisodeFilter.value === 'SUSTAINED') {
    list = list.filter((e) => e.duration_minutes >= 120)
  } else if (activeEpisodeFilter.value === 'CRITICAL') {
    list = list.filter((e) => e.max_residual > 30)
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter((e) => {
      const idMatch = String(e.event_id).includes(q) || `#${String(e.event_id).padStart(3, '0')}`.toLowerCase().includes(q)
      const unitMatch = (e.equipment_id || '').toLowerCase().includes(q)
      const timeMatch = (e.start_time || '').toLowerCase().includes(q)
      const typeMatch = (e.anomaly_type || '').toLowerCase().includes(q)
      return idMatch || unitMatch || timeMatch || typeMatch
    })
  }

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

// Displayed Episodes Slice
const displayedEvents = computed(() => {
  return filteredSortedEvents.value.slice(0, progressiveVisibleCount.value)
})

// Pagination Counts
const currentTableCount = computed(() => {
  return activeViewMode.value === 'classified'
    ? filteredClassified.value.length
    : filteredSortedEvents.value.length
})

const totalActiveListCount = computed(() => {
  return activeViewMode.value === 'classified'
    ? filteredClassified.value.length
    : filteredSortedEvents.value.length
})

const displayedCountText = computed(() => {
  const count = activeViewMode.value === 'classified'
    ? displayedClassified.value.length
    : displayedEvents.value.length
  return count > 0 ? `1–${count}` : '0'
})

const hasRemaining = computed(() => {
  const currentCount = activeViewMode.value === 'classified'
    ? displayedClassified.value.length
    : displayedEvents.value.length
  return currentCount < totalActiveListCount.value
})

const loadMore = () => {
  progressiveVisibleCount.value += 15
}

const collapseToInitial = () => {
  progressiveVisibleCount.value = 15
}

const resetProgressive = () => {
  progressiveVisibleCount.value = 15
}

// Styling Helpers
const getCategoryBadgeClass = (cat: string) => {
  switch (cat) {
    case 'power_surge':
      return 'bg-red-100 text-red-950 border-red-300 font-bold'
    case 'power_drop':
      return 'bg-blue-100 text-blue-950 border-blue-300 font-bold'
    case 'condenser':
      return 'bg-amber-100 text-amber-950 border-amber-300 font-bold'
    case 'pumping':
      return 'bg-cyan-100 text-cyan-950 border-cyan-300 font-bold'
    case 'flow_drop':
      return 'bg-purple-100 text-purple-950 border-purple-300 font-bold'
    case 'load_surge':
      return 'bg-indigo-100 text-indigo-950 border-indigo-300 font-bold'
    default:
      return 'bg-slate-100 text-slate-900 border-slate-300 font-semibold'
  }
}

const getDeviationColor = (anom: any) => {
  if (anom.category === 'power_surge' || anom.category === 'condenser') {
    return anom.anomaly_score >= 4.0 ? 'text-red-700' : 'text-amber-800'
  }
  if (anom.category === 'power_drop') {
    return 'text-blue-700'
  }
  if (anom.category === 'pumping') {
    return 'text-cyan-800'
  }
  return 'text-slate-900'
}

const formatDuration = (mins: number) => {
  const h = Math.floor(mins / 60)
  const m = mins % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

watch([activeViewMode, activeCategory], () => {
  resetProgressive()
})
</script>

<style scoped>
thead th,
.table-header-cell {
  background-color: #e2e8f0 !important;
  opacity: 1 !important;
  color: #0f172a !important;
}
</style>
