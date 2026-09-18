<template>
  <div class="bg-white border border-surface-200 rounded-xl p-5 shadow-card">
    
    <!-- Top Bar: Title, Context Toggles, Range Presets, Legend -->
    <div class="flex flex-col xl:flex-row xl:items-center xl:justify-between gap-3 pb-3.5 mb-2 border-b border-surface-200">
      <div>
        <div class="flex items-center space-x-2">
          <h3 class="text-sm font-bold text-surface-900 font-sans tracking-tight">
            Time-Series Telemetry & Contextual Energy Baseline
          </h3>
          <span class="text-[11px] px-2 py-0.5 rounded font-mono font-medium bg-surface-100 text-surface-600 border border-surface-200">
            Actual vs Expected kWh
          </span>
        </div>
        <p class="text-xs text-surface-500 mt-0.5">
          Select time range or click any observation to isolate contextual residuals and inspect model factors.
        </p>
      </div>

      <!-- Controls: Context Overlays + Range Presets -->
      <div class="flex flex-wrap items-center gap-2 text-xs">
        
        <!-- Context Sensor Toggle Buttons -->
        <div class="flex items-center bg-surface-100 p-0.5 rounded-lg border border-surface-200">
          <button
            @click="toggleOverlay('load')"
            :class="[
              'px-2.5 py-1 rounded text-[11px] font-medium transition-colors',
              activeOverlay === 'load'
                ? 'bg-white text-surface-900 shadow-xs border border-surface-200 font-semibold'
                : 'text-surface-600 hover:text-surface-900'
            ]"
          >
            Overlay Load (RT)
          </button>
          <button
            @click="toggleOverlay('flow')"
            :class="[
              'px-2.5 py-1 rounded text-[11px] font-medium transition-colors',
              activeOverlay === 'flow'
                ? 'bg-white text-surface-900 shadow-xs border border-surface-200 font-semibold'
                : 'text-surface-600 hover:text-surface-900'
            ]"
          >
            Overlay Flow (L/s)
          </button>
          <button
            @click="toggleOverlay('none')"
            :class="[
              'px-2 py-1 rounded text-[11px] font-medium transition-colors',
              activeOverlay === 'none'
                ? 'bg-white text-surface-900 shadow-xs border border-surface-200 font-semibold'
                : 'text-surface-500 hover:text-surface-800'
            ]"
          >
            Off
          </button>
        </div>

        <!-- Quick Range Presets -->
        <div class="flex items-center bg-surface-100 p-0.5 rounded-lg border border-surface-200 font-mono text-[11px]">
          <button
            v-for="preset in ['7D', '30D', '90D', 'ALL']"
            :key="preset"
            @click="setZoomPreset(preset)"
            :class="[
              'px-2 py-1 rounded transition-colors',
              activeRangePreset === preset
                ? 'bg-brand-600 text-white font-semibold shadow-xs'
                : 'text-surface-600 hover:text-surface-900'
            ]"
          >
            {{ preset }}
          </button>
        </div>

      </div>
    </div>

    <!-- Chart Legend & Status Indicator -->
    <div class="flex flex-wrap items-center justify-between gap-2 pb-2 text-xs font-mono">
      <div class="flex items-center space-x-4">
        <span class="flex items-center space-x-1.5">
          <span class="w-3 h-1 rounded-full bg-surface-900"></span>
          <span class="text-surface-700 font-medium">Measured Power (Actual)</span>
        </span>
        <span class="flex items-center space-x-1.5">
          <span class="w-3 h-1 rounded-full bg-brand-600"></span>
          <span class="text-surface-700 font-medium">Contextual Expected Baseline</span>
        </span>
        <span class="flex items-center space-x-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-status-orange border-2 border-white shadow-xs"></span>
          <span class="text-surface-700 font-medium">Abnormal Energy (|z| > 3.0)</span>
        </span>
        <span class="flex items-center space-x-1.5">
          <span class="w-2.5 h-2.5 rounded-full bg-status-amber border-2 border-white shadow-xs"></span>
          <span class="text-surface-700 font-medium">Low Confidence / Envelope</span>
        </span>
      </div>

      <div class="text-[11px] text-surface-500 font-sans">
        Click any point to inspect root-cause attribution
      </div>
    </div>

    <!-- Chart Canvas -->
    <div class="h-[480px] w-full relative">
      <ClientOnly>
        <v-chart
          v-if="telemetry.length > 0"
          ref="chartRef"
          :option="chartOption"
          autoresize
          class="h-full w-full"
          @click="onChartClick"
        />
        <div v-else class="h-full w-full flex items-center justify-center text-surface-400 text-sm font-mono">
          <div class="flex items-center space-x-2">
            <div class="w-2 h-2 rounded-full bg-brand-600 animate-ping"></div>
            <span>Loading telemetry stream...</span>
          </div>
        </div>
      </ClientOnly>
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
      lineStyle: { width: 2, color: '#0F172A' },
      z: 3
    },
    {
      name: 'Expected Baseline',
      type: 'line',
      data: expecteds,
      showSymbol: false,
      lineStyle: { width: 2, color: '#2563EB', type: 'solid' },
      areaStyle: {
        color: 'rgba(37, 99, 235, 0.04)'
      },
      z: 2
    },
    {
      name: 'Abnormal Energy Flag',
      type: 'scatter',
      data: anomalies,
      symbol: 'circle',
      symbolSize: 8,
      itemStyle: {
        color: '#EA580C',
        borderColor: '#FFFFFF',
        borderWidth: 1.5,
        shadowColor: 'rgba(234, 88, 12, 0.3)',
        shadowBlur: 4
      },
      z: 4
    },
    {
      name: 'Low Confidence Flag',
      type: 'scatter',
      data: lowConfMarkers,
      symbol: 'diamond',
      symbolSize: 7,
      itemStyle: {
        color: '#D97706',
        borderColor: '#FFFFFF',
        borderWidth: 1
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
          if (val > 25) return '#DC2626'   // Critical high
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
      lineStyle: { width: 1.5, color: '#64748B', type: 'dotted' },
      z: 1
    })
  } else if (activeOverlay.value === 'flow') {
    seriesList.push({
      name: 'Chilled Water Flow',
      type: 'line',
      yAxisIndex: 2,
      data: flows,
      showSymbol: false,
      lineStyle: { width: 1.5, color: '#0D9488', type: 'dotted' },
      z: 1
    })
  }

  const yAxes: any[] = [
    {
      type: 'value',
      name: 'Power (kWh)',
      nameTextStyle: { color: '#64748B', fontSize: 11, fontFamily: 'Plus Jakarta Sans', align: 'left', padding: [0, 0, 8, 0] },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'Fira Code' },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'solid' } }
    },
    {
      gridIndex: 1,
      type: 'value',
      name: 'Δ kWh',
      nameTextStyle: { color: '#64748B', fontSize: 10, fontFamily: 'Fira Code' },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 9, fontFamily: 'Fira Code' },
      splitLine: { lineStyle: { color: '#F1F5F9', type: 'solid' } }
    }
  ]

  if (activeOverlay.value !== 'none') {
    yAxes.push({
      type: 'value',
      position: 'right',
      name: activeOverlay.value === 'load' ? 'Load (RT)' : 'Flow (L/s)',
      nameTextStyle: { color: activeOverlay.value === 'load' ? '#64748B' : '#0D9488', fontSize: 10 },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'Fira Code' },
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
      padding: 12,
      shadowColor: 'rgba(15, 23, 42, 0.08)',
      shadowBlur: 16,
      textStyle: { color: '#0F172A', fontFamily: 'Plus Jakarta Sans', fontSize: 12 },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const idx = params[0].dataIndex
        const item = props.telemetry[idx]
        if (!item) return ''

        const isAnom = item.anom === 1
        const statusLabel = item.status || (isAnom ? 'ABNORMAL ENERGY' : 'NORMAL')
        let statusBadge = `<span style="background: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">NORMAL</span>`
        if (statusLabel === 'ABNORMAL ENERGY') {
          statusBadge = `<span style="background: #FFF7ED; color: #9A3412; border: 1px solid #FED7AA; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">ABNORMAL ENERGY</span>`
        } else if (statusLabel === 'LOW CONFIDENCE') {
          statusBadge = `<span style="background: #FFFBEB; color: #92400E; border: 1px solid #FDE68A; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">LOW CONFIDENCE</span>`
        } else if (statusLabel === 'DATA + ENERGY ISSUE') {
          statusBadge = `<span style="background: #FEF2F2; color: #991B1B; border: 1px solid #FECACA; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">DATA + ENERGY ISSUE</span>`
        }

        return `
          <div style="font-family: 'Plus Jakarta Sans', system-ui, sans-serif; min-width: 240px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; border-bottom: 1px solid #F1F5F9; padding-bottom: 4px;">
              <span style="font-family: 'Fira Code', monospace; color: #64748B; font-size: 11px;">${item.ts}</span>
              ${statusBadge}
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-family: 'Fira Code', monospace; margin-bottom: 8px;">
              <div>
                <span style="color: #64748B; font-size: 10px; display: block;">Measured Power</span>
                <span style="font-weight: 700; color: #0F172A; font-size: 13px;">${item.act} kWh</span>
              </div>
              <div>
                <span style="color: #64748B; font-size: 10px; display: block;">Expected Baseline</span>
                <span style="font-weight: 700; color: #2563EB; font-size: 13px;">${item.exp} kWh</span>
              </div>
            </div>

            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 6px 8px; margin-bottom: 8px;">
              <div style="display: flex; justify-content: space-between; font-family: 'Fira Code', monospace; font-size: 11px;">
                <span style="color: #64748B;">Contextual Residual:</span>
                <span style="font-weight: 700; color: ${item.res > 15 ? '#DC2626' : item.res > 0 ? '#EA580C' : '#059669'};">
                  ${item.res > 0 ? '+' : ''}${item.res} kWh (z=${item.z})
                </span>
              </div>
            </div>

            <div style="font-size: 10.5px; color: #64748B; line-height: 1.5; border-top: 1px solid #F1F5F9; padding-top: 6px;">
              <div>Building Load: <strong style="color: #334155;">${item.load ?? '--'} RT</strong> • Flow: <strong style="color: #334155;">${item.flow ?? '--'} L/s</strong></div>
              <div>Cooling Water: <strong style="color: #334155;">${item.cw_temp ?? '--'}°C</strong> • Wet-Bulb: <strong style="color: #334155;">${item.wb_temp ?? '--'}°C</strong></div>
            </div>
          </div>
        `
      }
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '55', right: activeOverlay.value !== 'none' ? '55' : '25', top: '25', height: '58%' },
      { left: '55', right: activeOverlay.value !== 'none' ? '55' : '25', top: '78%', height: '14%' }
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
        axisLabel: { color: '#64748B', fontSize: 10, fontFamily: 'Fira Code' },
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
        height: 18,
        borderColor: '#E2E8F0',
        backgroundColor: '#F8FAFC',
        fillerColor: 'rgba(37, 99, 235, 0.12)',
        handleStyle: { color: '#2563EB', borderColor: '#FFFFFF', borderWidth: 1 },
        textStyle: { color: 'transparent' },
        start: zoomRange.value[0],
        end: zoomRange.value[1]
      }
    ],
    series: seriesList
  }
})
</script>
