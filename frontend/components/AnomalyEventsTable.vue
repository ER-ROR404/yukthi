<template>
  <div class="bg-white border border-surface-200 rounded-xl p-5 sm:p-6 shadow-card">
    
    <!-- Table Header & Controls -->
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 pb-4 mb-3.5 border-b border-surface-200">
      <div>
        <div class="flex items-center space-x-2.5">
          <h3 class="text-base sm:text-lg font-bold text-surface-900 font-sans tracking-tight">
            Persistent Operational Anomaly Episodes
          </h3>
          <span class="text-xs px-2.5 py-0.5 rounded font-mono font-semibold bg-surface-100 text-surface-800 border border-surface-200">
            {{ filteredSortedEvents.length }} Consolidated Episodes
          </span>
        </div>
        <p class="text-xs sm:text-sm text-surface-600 mt-0.5 font-sans">
          Consecutive sustained deviations grouped into consolidated maintenance events (avoids noisy point alerts).
        </p>
      </div>

      <!-- Search & Filter Bar -->
      <div class="flex flex-wrap items-center gap-2">
        <!-- Quick Search -->
        <div class="relative">
          <Search class="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-surface-400" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search #, date, severity..."
            class="text-xs sm:text-sm pl-8 pr-7 py-1.5 rounded-lg border border-surface-200 bg-surface-50 focus:bg-white focus:outline-none focus:border-brand-500 font-sans w-48 sm:w-56 transition-colors"
          />
          <button
            v-if="searchQuery"
            @click="searchQuery = ''"
            class="absolute right-2 top-1/2 -translate-y-1/2 text-surface-400 hover:text-surface-700 p-0.5 cursor-pointer"
            title="Clear search"
          >
            <X class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Filter Tabs -->
        <div class="flex items-center bg-surface-100 p-1 rounded-lg border border-surface-200 text-xs sm:text-sm font-medium">
          <button
            v-for="filter in filters"
            :key="filter.id"
            @click="setFilter(filter.id)"
            :class="[
              'px-2.5 py-1 rounded-md transition-colors cursor-pointer',
              activeFilter === filter.id
                ? 'bg-white text-surface-900 shadow-xs font-bold'
                : 'text-surface-600 hover:text-surface-900'
            ]"
          >
            {{ filter.label }}
          </button>
        </div>
      </div>
    </div>

    <!-- Interactive Event Table -->
    <div
      :class="[
        'overflow-x-auto border border-surface-200 rounded-lg transition-all',
        displayedEvents.length > 25 ? 'max-h-[560px] overflow-y-auto' : ''
      ]"
    >
      <table class="w-full text-left text-xs sm:text-sm font-mono border-collapse">
        <thead class="sticky top-0 z-20 font-sans shadow-xs">
          <tr class="border-b border-surface-300">
            <th
              @click="toggleSort('event_id')"
              class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-surface-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Event</span>
                <component :is="getSortIcon('event_id')" class="w-3 h-3 text-surface-500" />
              </div>
            </th>
            <th class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider">Unit</th>
            <th
              @click="toggleSort('start_time')"
              class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-surface-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Start Time Window</span>
                <component :is="getSortIcon('start_time')" class="w-3 h-3 text-surface-500" />
              </div>
            </th>
            <th
              @click="toggleSort('duration_minutes')"
              class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider cursor-pointer select-none hover:text-surface-950 transition-colors"
            >
              <div class="flex items-center space-x-1">
                <span>Duration</span>
                <component :is="getSortIcon('duration_minutes')" class="w-3 h-3 text-surface-500" />
              </div>
            </th>
            <th
              @click="toggleSort('max_residual')"
              class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider text-right cursor-pointer select-none hover:text-surface-950 transition-colors"
            >
              <div class="flex items-center justify-end space-x-1">
                <span>Peak Dev</span>
                <component :is="getSortIcon('max_residual')" class="w-3 h-3 text-surface-500" />
              </div>
            </th>
            <th class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider text-right">Mean Dev</th>
            <th class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider text-center">Severity</th>
            <th class="bg-surface-100 py-3 px-3.5 font-semibold text-surface-700 uppercase text-xs tracking-wider text-right">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-surface-100 text-surface-800">
          <tr
            v-for="ev in displayedEvents"
            :key="ev.event_id"
            @click="$emit('select-event', ev)"
            :class="[
              'transition-colors cursor-pointer text-xs sm:text-sm',
              selectedEventId === ev.event_id
                ? 'bg-brand-50 font-medium border-l-4 border-brand-600'
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
                class="px-3 py-1.5 rounded-md bg-brand-50 text-brand-700 hover:bg-brand-100 text-xs font-bold border border-brand-200 transition-colors cursor-pointer"
                @click.stop="$emit('select-event', ev)"
              >
                Inspect
              </button>
            </td>
          </tr>

          <tr v-if="displayedEvents.length === 0">
            <td colspan="8" class="py-10 text-center text-surface-500 font-sans text-sm">
              <div class="space-y-2">
                <p>No anomaly events match the selected criteria.</p>
                <button
                  v-if="searchQuery || activeFilter !== 'ALL'"
                  @click="resetFilters"
                  class="text-xs font-semibold text-brand-600 hover:underline cursor-pointer"
                >
                  Reset filters & search
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Table Footer: Progressive Disclosure ('See More') & Splitting (Pagination) -->
    <div class="mt-4 pt-3.5 border-t border-surface-200 space-y-3">
      
      <!-- Primary Action Bar: 'See More' & Progressive Status -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 bg-surface-50 p-3 rounded-lg border border-surface-200">
        
        <!-- Status Indicator -->
        <div class="flex items-center space-x-3 text-xs sm:text-sm font-sans">
          <span class="text-surface-700">
            Showing
            <strong class="font-mono text-surface-900 font-bold">{{ displayedRangeText }}</strong>
            of
            <strong class="font-mono text-surface-900 font-bold">{{ filteredSortedEvents.length }}</strong>
            episodes
          </span>
          
          <span
            v-if="remainingCount > 0"
            class="text-xs font-mono text-surface-700 bg-surface-200 px-2 py-0.5 rounded font-medium"
          >
            {{ remainingCount }} remaining
          </span>
          <span
            v-else-if="filteredSortedEvents.length > 0"
            class="text-xs font-mono text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded font-semibold"
          >
            All Loaded
          </span>
        </div>

        <!-- Interactive See More & Quick Actions -->
        <div class="flex items-center space-x-2">
          
          <!-- See More Button (appends next 10 episodes in place) -->
          <button
            v-if="remainingCount > 0"
            @click="loadMore"
            class="flex items-center space-x-1.5 px-3.5 py-1.5 bg-white hover:bg-surface-100 text-surface-900 font-semibold text-xs sm:text-sm rounded-md border border-surface-300 shadow-xs transition-colors cursor-pointer"
          >
            <span>See More (+{{ Math.min(10, remainingCount) }})</span>
            <ChevronDown class="w-3.5 h-3.5 text-surface-600" />
          </button>

          <!-- See All Button -->
          <button
            v-if="remainingCount > 0"
            @click="showAll"
            class="px-2.5 py-1.5 text-xs sm:text-sm font-medium text-brand-600 hover:text-brand-800 hover:underline cursor-pointer"
          >
            See All ({{ filteredSortedEvents.length }})
          </button>

          <!-- Collapse Button (when expanded beyond initial batch) -->
          <button
            v-if="isExpandedBeyondInitial"
            @click="collapseToInitial"
            class="flex items-center space-x-1.5 px-3 py-1.5 bg-surface-200 hover:bg-surface-300 text-surface-800 font-semibold text-xs sm:text-sm rounded-md border border-surface-300 transition-colors cursor-pointer"
          >
            <span>Collapse to {{ defaultBatchSize }}</span>
            <ChevronUp class="w-3.5 h-3.5 text-surface-600" />
          </button>

        </div>

      </div>

      <!-- Secondary Controls: Batch Size & Page Switching -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs sm:text-sm font-sans pt-0.5">
        
        <!-- Batch Size Selector -->
        <div class="flex items-center space-x-2 text-surface-600">
          <span>Split batch:</span>
          <div class="inline-flex rounded-md border border-surface-200 bg-surface-100 p-0.5 font-mono text-xs">
            <button
              v-for="size in [10, 25, 50]"
              :key="size"
              @click="setBatchSize(size)"
              :class="[
                'px-2.5 py-1 rounded transition-colors cursor-pointer',
                defaultBatchSize === size && !isViewingAll
                  ? 'bg-white text-surface-900 shadow-xs font-bold'
                  : 'text-surface-600 hover:text-surface-900'
              ]"
            >
              {{ size }}
            </button>
          </div>
        </div>

        <!-- Page Navigator (when navigating split pages) -->
        <div v-if="totalPages > 1 && !isExpandedMode" class="flex items-center space-x-1">
          <button
            @click="prevPage"
            :disabled="currentPage === 1"
            class="px-2.5 py-1 rounded border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs font-medium flex items-center space-x-1 cursor-pointer"
          >
            <ChevronLeft class="w-3.5 h-3.5" />
            <span>Prev</span>
          </button>

          <span class="px-2.5 py-1 text-surface-700 font-mono text-xs sm:text-sm">
            Page <strong class="text-surface-900 font-bold">{{ currentPage }}</strong> of <strong class="text-surface-900 font-bold">{{ totalPages }}</strong>
          </span>

          <button
            @click="nextPage"
            :disabled="currentPage === totalPages"
            class="px-2.5 py-1 rounded border border-surface-200 bg-white text-surface-700 hover:bg-surface-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-xs font-medium flex items-center space-x-1 cursor-pointer"
          >
            <span>Next</span>
            <ChevronRight class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- Footnote trigger -->
        <div class="text-xs text-surface-500 font-mono">
          Trigger: Robust MAD > 3.0 (7-day baseline)
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
  ChevronLeft,
  ChevronRight,
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

// Splitting & Progressive Disclosure ("See More") State
const defaultBatchSize = ref(10)
const currentPage = ref(1)
const isExpandedMode = ref(false)
const progressiveVisibleCount = ref(10)
const isViewingAll = ref(false)

const setFilter = (id: string) => {
  activeFilter.value = id
  resetPagination()
}

const resetFilters = () => {
  activeFilter.value = 'ALL'
  searchQuery.value = ''
  resetPagination()
}

const resetPagination = () => {
  currentPage.value = 1
  isExpandedMode.value = false
  isViewingAll.value = false
  progressiveVisibleCount.value = defaultBatchSize.value
}

// Formatters
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

// Total Pages based on current batch size
const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredSortedEvents.value.length / defaultBatchSize.value))
})

// Computed: Final Displayed Events (either progressive 'See More' slice or Paginated slice)
const displayedEvents = computed(() => {
  const total = filteredSortedEvents.value.length
  if (total === 0) return []

  if (isExpandedMode.value || isViewingAll.value) {
    return filteredSortedEvents.value.slice(0, progressiveVisibleCount.value)
  }

  const start = (currentPage.value - 1) * defaultBatchSize.value
  return filteredSortedEvents.value.slice(start, start + defaultBatchSize.value)
})

// Remaining items count
const remainingCount = computed(() => {
  const total = filteredSortedEvents.value.length
  if (isExpandedMode.value || isViewingAll.value) {
    return Math.max(0, total - progressiveVisibleCount.value)
  }
  return Math.max(0, total - (currentPage.value * defaultBatchSize.value))
})

// Range text (e.g. "1–10" or "1–30")
const displayedRangeText = computed(() => {
  const count = displayedEvents.value.length
  if (count === 0) return '0'
  if (isExpandedMode.value || isViewingAll.value) {
    return `1–${count}`
  }
  const start = (currentPage.value - 1) * defaultBatchSize.value + 1
  const end = Math.min(filteredSortedEvents.value.length, start + count - 1)
  return `${start}–${end}`
})

const isExpandedBeyondInitial = computed(() => {
  if (isExpandedMode.value || isViewingAll.value) {
    return progressiveVisibleCount.value > defaultBatchSize.value
  }
  return false
})

// User Actions
const loadMore = () => {
  if (!isExpandedMode.value) {
    isExpandedMode.value = true
    progressiveVisibleCount.value = Math.min(
      filteredSortedEvents.value.length,
      (currentPage.value * defaultBatchSize.value) + 10
    )
  } else {
    progressiveVisibleCount.value = Math.min(
      filteredSortedEvents.value.length,
      progressiveVisibleCount.value + 10
    )
  }
}

const showAll = () => {
  isViewingAll.value = true
  isExpandedMode.value = true
  progressiveVisibleCount.value = filteredSortedEvents.value.length
}

const collapseToInitial = () => {
  isViewingAll.value = false
  isExpandedMode.value = false
  progressiveVisibleCount.value = defaultBatchSize.value
  currentPage.value = 1
}

const setBatchSize = (size: number) => {
  defaultBatchSize.value = size
  progressiveVisibleCount.value = size
  currentPage.value = 1
  isExpandedMode.value = false
  isViewingAll.value = false
}

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
  }
}

// Watchers: Keep selection in view when selectedEventId changes
watch(
  () => props.selectedEventId,
  (newId) => {
    if (newId === undefined || newId === null) return
    const idx = filteredSortedEvents.value.findIndex((e) => e.event_id === newId)
    if (idx >= 0) {
      if (isExpandedMode.value) {
        if (progressiveVisibleCount.value <= idx) {
          progressiveVisibleCount.value = Math.ceil((idx + 1) / 10) * 10
        }
      } else {
        currentPage.value = Math.floor(idx / defaultBatchSize.value) + 1
      }
    }
  }
)

// Reset pagination when raw equipment events prop changes
watch(
  () => props.events,
  () => {
    resetPagination()
  }
)
</script>

<style scoped>
thead th {
  background-color: #f1f5f9 !important;
  opacity: 1 !important;
}
</style>
