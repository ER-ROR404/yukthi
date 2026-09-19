<template>
  <div class="card-solid bg-white border border-slate-300 rounded-xl overflow-hidden shadow-xs hover:border-slate-400 transition-colors">
    
    <!-- Top Bar: Title, Context Toggles, Range Presets -->
    <div class="px-5 sm:px-6 py-4 sm:py-5 bg-slate-100 border-b border-slate-300 space-y-3">
      
      <!-- Top Title Row: Guaranteed 1 Line -->
      <div class="flex items-center justify-between">
        <h3 class="text-base sm:text-lg xl:text-xl font-bold text-slate-950 font-sans tracking-tight whitespace-nowrap">
          Time-Series Telemetry & Contextual Energy Baseline
        </h3>
      </div>

      <!-- Controls Row: Context Overlays + Range Presets -->
      <div class="pt-2.5 border-t border-slate-200/80 flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
        
        <!-- Context Sensor Toggle Buttons -->
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-600 font-sans hidden sm:inline-block">Overlay:</span>
          <div class="flex items-center bg-slate-200/80 p-1 rounded-lg border border-slate-300">
            <button
              @click="toggleOverlay('load')"
              :class="[
                'px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors cursor-pointer',
                activeOverlay === 'load'
                  ? 'bg-white text-slate-950 shadow-xs border border-slate-300 font-bold'
                  : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
              ]"
            >
              Overlay Load (RT)
            </button>
            <button
              @click="toggleOverlay('flow')"
              :class="[
                'px-3 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors cursor-pointer',
                activeOverlay === 'flow'
                  ? 'bg-white text-slate-950 shadow-xs border border-slate-300 font-bold'
                  : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
              ]"
            >
              Overlay Flow (L/s)
            </button>
            <button
              @click="toggleOverlay('none')"
              :class="[
                'px-2.5 py-1.5 rounded-md text-xs sm:text-sm font-medium transition-colors cursor-pointer',
                activeOverlay === 'none'
                  ? 'bg-white text-slate-950 shadow-xs border border-slate-300 font-bold'
                  : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
              ]"
            >
              Off
            </button>
          </div>
        </div>

        <!-- Quick Range Presets -->
        <div class="flex items-center space-x-2">
          <span class="text-xs font-bold uppercase tracking-wider text-slate-600 font-sans hidden sm:inline-block">Range:</span>
          <div class="flex items-center bg-slate-200/80 p-1 rounded-lg border border-slate-300 font-mono text-xs sm:text-sm">
            <button
              v-for="preset in ['7D', '30D', '90D', 'ALL']"
              :key="preset"
              @click="setZoomPreset(preset)"
              :class="[
                'px-3 py-1.5 rounded-md transition-colors cursor-pointer font-bold',
                activeRangePreset === preset
                  ? 'bg-blue-600 text-white shadow-xs'
                  : 'text-slate-700 hover:text-slate-950 hover:bg-slate-300/60'
              ]"
            >
              {{ preset }}
            </button>
          </div>
        </div>

      </div>
    </div>

    <!-- Chart Body Container with clean padding -->
    <div class="p-5 sm:p-6 space-y-4">
      <!-- Chart Legend & Status Indicator -->
      <div class="flex flex-wrap items-center justify-between gap-3 pb-2 text-xs sm:text-sm">
        <div class="flex flex-wrap items-center gap-x-5 gap-y-2">
          <span class="flex items-center space-x-2">
            <span class="w-3.5 h-1 rounded-full bg-red-600"></span>
            <span class="text-slate-900 font-semibold">Measured Power (Actual)</span>
          </span>
          <span class="flex items-center space-x-2">
            <span class="w-3.5 h-1 rounded-full bg-blue-600"></span>
            <span class="text-slate-900 font-semibold">Contextual Expected Baseline</span>
          </span>
          <span class="flex items-center space-x-2">
            <span class="w-3 h-3 rounded-full bg-orange-600 border-2 border-white shadow-xs"></span>
            <span class="text-slate-800 font-medium">Abnormal Energy (|z| > 3.0)</span>
          </span>
          <span class="flex items-center space-x-2">
            <span class="w-2.5 h-2.5 rotate-45 bg-purple-600 border border-white shadow-xs"></span>
            <span class="text-slate-800 font-medium">Low Confidence / Envelope Flag</span>
          </span>
        </div>

        <div class="text-xs sm:text-sm text-slate-600 font-sans font-medium hidden md:block">
          Click any data point to inspect model factors
        </div>
      </div>

      <!-- Chart Canvas -->
      <div class="h-[500px] w-full relative">
        <ClientOnly>
          <v-chart
            v-if="telemetry.length > 0"
            ref="chartRef"
            :option="chartOption"
            autoresize
            class="h-full w-full"
            @click="onChartClick"
          />
          <div v-else class="h-full w-full flex items-center justify-center text-surface-500 text-sm font-mono">
            <div class="flex items-center space-x-2">
              <div class="w-2.5 h-2.5 rounded-full bg-brand-600 animate-ping"></div>
              <span>Loading telemetry stream...</span>
            </div>
          </div>
        </ClientOnly>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  telemetry: Array<{
    ts: string
    act: number
    exp: number
    res: number
    z: number
    anom: number
    status?: string
    low_conf?: number
    load: number | null
    flow: number | null
    cw_temp: number | null
    out_temp: number | null
    wb_temp: number | null
  }>
}>()

const emit = defineEmits<{
  (e: 'inspect-point', point: any): void
}>()

const chartRef = ref<any>(null)
const activeOverlay = ref<'none' | 'load' | 'flow'>('none')
const activeRangePreset = ref<'7D' | '30D' | '90D' | 'ALL'>('30D')
const zoomRange = ref<[number, number]>([0, 25])

const toggleOverlay = (type: 'none' | 'load' | 'flow') => {
  activeOverlay.value = type
}

const setZoomPreset = (preset: '7D' | '30D' | '90D' | 'ALL') => {
  activeRangePreset.value = preset
  const total = props.telemetry.length
  if (total === 0) return

  // 48 observations per day (30-min intervals)
  if (preset === '7D') {
    const pct = Math.min(100, (48 * 7 / total) * 100)
    zoomRange.value = [0, pct]
  } else if (preset === '30D') {
    const pct = Math.min(100, (48 * 30 / total) * 100)
    zoomRange.value = [0, pct]
  } else if (preset === '90D') {
    const pct = Math.min(100, (48 * 90 / total) * 100)
    zoomRange.value = [0, pct]
  } else {
    zoomRange.value = [0, 100]
  }
}

const onChartClick = (params: any) => {
  if (params.dataIndex !== undefined && props.telemetry[params.dataIndex]) {
    emit('inspect-point', props.telemetry[params.dataIndex])
  }
}

const chartOption = computed(() => {
  const data = props.telemetry
  const timestamps = data.map((d) => d.ts.substring(0, 16).replace('T', ' '))
  const actuals = data.map((d) => d.act)
  const expecteds = data.map((d) => d.exp)
  const residuals = data.map((d) => d.res)
  
  // Energy anomaly markers (|z| > 3.0 or anom === 1)
  const anomalies = data.map((d) => (d.anom === 1 && d.status !== 'LOW CONFIDENCE' ? d.act : null))
  // Low confidence / envelope markers
  const lowConfMarkers = data.map((d) => (d.status === 'LOW CONFIDENCE' || d.low_conf === 1 ? d.act : null))

  // Contextual overlays
  const loads = data.map((d) => d.load)
  const flows = data.map((d) => d.flow)

  const seriesList: any[] = [
    {
      name: 'Measured Power',
      type: 'line',
      data: actuals,
      showSymbol: false,
      lineStyle: { width: 2.2, color: '#DC2626' }, // Vibrant industrial RED as requested
      z: 3
    },
    {
      name: 'Expected Baseline',
      type: 'line',
      data: expecteds,
      showSymbol: false,
      lineStyle: { width: 2.2, color: '#2563EB', type: 'solid' },
      areaStyle: {
        color: 'rgba(37, 99, 235, 0.05)'
      },
      z: 2
    },
    {
      name: 'Abnormal Energy Flag',
      type: 'scatter',
      data: anomalies,
      symbol: 'circle',
      symbolSize: 9,
      itemStyle: {
        color: '#EA580C',
        borderColor: '#FFFFFF',
        borderWidth: 2,
        shadowColor: 'rgba(234, 88, 12, 0.35)',
        shadowBlur: 5
      },
      z: 4
    },
    {
      name: 'Low Confidence Flag',
      type: 'scatter',
      data: lowConfMarkers,
      symbol: 'diamond',
      symbolSize: 10,
      itemStyle: {
        color: '#7C3AED',
        borderColor: '#FFFFFF',
        borderWidth: 2,
        shadowColor: 'rgba(124, 58, 237, 0.4)',
        shadowBlur: 6
      },
      z: 4
    },
    {
      name: 'Residual',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: residuals,
      itemStyle: {
        color: (params: any) => {
          const val = params.value
          if (val > 25) return '#DC2626'   // Severe high
          if (val > 10) return '#EA580C'   // Abnormal
          if (val < -15) return '#0284C7'  // Deep negative
          return '#94A3B8'                // Nominal
        }
      }
    }
  ]

  // Optional Context Sensor Overlay on Secondary Y-Axis
  if (activeOverlay.value === 'load') {
    seriesList.push({
      name: 'Building Load',
      type: 'line',
      yAxisIndex: 2,
      data: loads,
      showSymbol: false,
      lineStyle: { width: 1.8, color: '#64748B', type: 'dashed' },
      z: 1
    })
  } else if (activeOverlay.value === 'flow') {
    seriesList.push({
      name: 'Chilled Water Flow',
      type: 'line',
      yAxisIndex: 2,
      data: flows,
      showSymbol: false,
      lineStyle: { width: 1.8, color: '#0D9488', type: 'dashed' },
      z: 1
    })
  }

  const yAxes: any[] = [
    {
      type: 'value',
      name: 'Power (kWh)',
      nameTextStyle: { color: '#475569', fontSize: 12, fontFamily: 'Inter, system-ui, sans-serif', align: 'left', padding: [0, 0, 8, 0], fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#475569', fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fontWeight: 500 },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'solid' } }
    },
    {
      gridIndex: 1,
      type: 'value',
      name: 'Δ kWh',
      nameTextStyle: { color: '#64748B', fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fontWeight: 500 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'JetBrains Mono, monospace' },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'solid' } }
    }
  ]

  if (activeOverlay.value !== 'none') {
    yAxes.push({
      type: 'value',
      position: 'right',
      name: activeOverlay.value === 'load' ? 'Load (RT)' : 'Flow (L/s)',
      nameTextStyle: { color: activeOverlay.value === 'load' ? '#475569' : '#0D9488', fontSize: 12, fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 600 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 11, fontFamily: 'JetBrains Mono, monospace' },
      splitLine: { show: false }
    })
  }

  return {
    backgroundColor: '#FFFFFF',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: { color: '#CBD5E1', width: 1, type: 'dashed' }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#E2E8F0',
      borderWidth: 1,
      padding: 14,
      shadowColor: 'rgba(15, 23, 42, 0.08)',
      shadowBlur: 16,
      textStyle: { color: '#0F172A', fontFamily: 'Inter, system-ui, sans-serif', fontSize: 13 },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const idx = params[0].dataIndex
        const item = props.telemetry[idx]
        if (!item) return ''

        const isAnom = item.anom === 1
        const statusLabel = item.status || (isAnom ? 'ABNORMAL ENERGY' : 'NORMAL')
        let statusBadge = `<span style="background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">NORMAL</span>`
        if (statusLabel === 'ABNORMAL ENERGY') {
          statusBadge = `<span style="background: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">ABNORMAL ENERGY</span>`
        } else if (statusLabel === 'LOW CONFIDENCE') {
          statusBadge = `<span style="background: #F3E8FF; color: #6B21A8; border: 1px solid #D8B4FE; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">LOW CONFIDENCE</span>`
        } else if (statusLabel === 'DATA + ENERGY ISSUE') {
          statusBadge = `<span style="background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;">DATA + ENERGY ISSUE</span>`
        }

        return `
          <div style="font-family: 'Inter', system-ui, sans-serif; min-width: 260px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid #F1F5F9; padding-bottom: 6px;">
              <span style="font-family: 'JetBrains Mono', monospace; font-feature-settings: 'tnum' 1; color: #475569; font-size: 12px; font-weight: 600;">${item.ts}</span>
              ${statusBadge}
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-family: 'JetBrains Mono', monospace; font-feature-settings: 'tnum' 1; margin-bottom: 10px;">
              <div>
                <span style="color: #DC2626; font-size: 11px; display: block; font-weight: 600;">Measured Power</span>
                <span style="font-weight: 700; color: #DC2626; font-size: 15px;">${item.act} kWh</span>
              </div>
              <div>
                <span style="color: #2563EB; font-size: 11px; display: block; font-weight: 600;">Expected Baseline</span>
                <span style="font-weight: 700; color: #2563EB; font-size: 15px;">${item.exp} kWh</span>
              </div>
            </div>

            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px 10px; margin-bottom: 10px;">
              <div style="display: flex; justify-content: space-between; font-family: 'JetBrains Mono', monospace; font-feature-settings: 'tnum' 1; font-size: 12px;">
                <span style="color: #475569; font-weight: 500;">Contextual Residual:</span>
                <span style="font-weight: 700; color: ${item.res > 15 ? '#DC2626' : item.res > 0 ? '#EA580C' : '#059669'}; font-size: 13px;">
                  ${item.res > 0 ? '+' : ''}${item.res} kWh (z=${item.z})
                </span>
              </div>
            </div>

            <div style="font-size: 11.5px; color: #475569; line-height: 1.6; border-top: 1px solid #F1F5F9; padding-top: 8px;">
              <div>Building Load: <strong style="color: #0F172A;">${item.load ?? '--'} RT</strong> • Flow: <strong style="color: #0F172A;">${item.flow ?? '--'} L/s</strong></div>
              <div>Cooling Water: <strong style="color: #0F172A;">${item.cw_temp ?? '--'}°C</strong> • Wet-Bulb: <strong style="color: #0F172A;">${item.wb_temp ?? '--'}°C</strong></div>
            </div>
          </div>
        `
      }
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '60', right: activeOverlay.value !== 'none' ? '60' : '25', top: '25', height: '58%' },
      { left: '60', right: activeOverlay.value !== 'none' ? '60' : '25', top: '78%', height: '14%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: timestamps,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { show: false },
        splitLine: { show: true, lineStyle: { color: '#F8FAFC' } }
      },
      {
        gridIndex: 1,
        type: 'category',
        data: timestamps,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#CBD5E1' } },
        axisLabel: { color: '#475569', fontSize: 11, fontFamily: 'JetBrains Mono, monospace', fontWeight: 500 },
        splitLine: { show: true, lineStyle: { color: '#F8FAFC' } }
      }
    ],
    yAxis: yAxes,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: zoomRange.value[0],
        end: zoomRange.value[1]
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 2,
        height: 20,
        borderColor: '#E2E8F0',
        backgroundColor: '#F8FAFC',
        fillerColor: 'rgba(37, 99, 235, 0.12)',
        handleStyle: { color: '#2563EB', borderColor: '#FFFFFF', borderWidth: 1.5 },
        textStyle: { color: 'transparent' },
        start: zoomRange.value[0],
        end: zoomRange.value[1]
      }
    ],
    series: seriesList
  }
})
</script>
