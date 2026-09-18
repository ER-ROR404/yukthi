<template>
  <div class="bg-cockpit-900 border border-cockpit-800 rounded-lg p-4">
    <!-- Header with Legend and Info -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pb-3 mb-2 border-b border-cockpit-800/60">
      <div>
        <h3 class="text-sm font-semibold text-cockpit-100 flex items-center space-x-2">
          <span>Telemetry Stream: Actual vs Expected Baseline & Residual Deviation</span>
        </h3>
        <p class="text-xs text-cockpit-300">
          60fps timeline with synchronized crosshairs. Click any anomaly to view instant SHAP feature attribution.
        </p>
      </div>

      <!-- Quick stats legend -->
      <div class="flex items-center space-x-3 text-xs font-mono">
        <span class="flex items-center space-x-1">
          <span class="w-2.5 h-2.5 rounded-full bg-status-crimson"></span>
          <span class="text-cockpit-300">Actual (kWh)</span>
        </span>
        <span class="flex items-center space-x-1">
          <span class="w-2.5 h-0.5 bg-status-blue"></span>
          <span class="text-cockpit-300">Expected (kWh)</span>
        </span>
        <span class="flex items-center space-x-1">
          <span class="w-2.5 h-2.5 bg-status-amber rotate-45"></span>
          <span class="text-cockpit-300">Anomaly (|z| > 2.5)</span>
        </span>
      </div>
    </div>

    <!-- Chart Container -->
    <div class="h-[460px] w-full relative">
      <ClientOnly>
        <v-chart
          v-if="telemetry.length > 0"
          :option="chartOption"
          autoresize
          class="h-full w-full"
          @click="onChartClick"
        />
        <div v-else class="h-full w-full flex items-center justify-center text-cockpit-300 text-sm font-mono">
          <div class="animate-pulse">Loading telemetry records...</div>
        </div>
      </ClientOnly>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  telemetry: Array<{
    ts: string
    act: number
    exp: number
    res: number
    z: number
    anom: number
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

const onChartClick = (params: any) => {
  if (params.dataIndex !== undefined && props.telemetry[params.dataIndex]) {
    emit('inspect-point', props.telemetry[params.dataIndex])
  }
}

const chartOption = computed(() => {
  const timestamps = props.telemetry.map((d) => d.ts.replace('T', ' ').substring(5, 16))
  const actuals = props.telemetry.map((d) => d.act)
  const expecteds = props.telemetry.map((d) => d.exp)
  const residuals = props.telemetry.map((d) => d.res)
  const anomalies = props.telemetry.map((d) => (d.anom === 1 ? d.act : null))

  return {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross',
        lineStyle: { color: '#334460', width: 1 }
      },
      backgroundColor: '#0F1622',
      borderColor: '#24324A',
      textStyle: { color: '#F1F5F9', fontFamily: 'Fira Code', fontSize: 11 },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const idx = params[0].dataIndex
        const item = props.telemetry[idx]
        if (!item) return ''

        return `
          <div style="font-family: 'Fira Code', monospace; line-height: 1.4; padding: 2px;">
            <div style="color: #94A3B8; font-size: 10px; margin-bottom: 4px;">${item.ts}</div>
            <div style="display: flex; justify-content: space-between; gap: 12px;">
              <span style="color: #EF4444;">Actual:</span>
              <span style="font-weight: bold;">${item.act} kWh</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 12px;">
              <span style="color: #3B82F6;">Expected:</span>
              <span style="font-weight: bold;">${item.exp} kWh</span>
            </div>
            <div style="display: flex; justify-content: space-between; gap: 12px;">
              <span style="color: ${item.res > 0 ? '#F59E0B' : '#10B981'};">Deviation:</span>
              <span style="font-weight: bold;">${item.res > 0 ? '+' : ''}${item.res} kWh (z=${item.z})</span>
            </div>
            <hr style="border: 0; border-top: 1px solid #24324A; margin: 4px 0;" />
            <div style="font-size: 10px; color: #94A3B8;">
              Load: ${item.load ?? '--'} RT • Flow: ${item.flow ?? '--'} L/s<br/>
              Cooling H2O: ${item.cw_temp ?? '--'}°C • Outside: ${item.out_temp ?? '--'}°F
            </div>
            ${item.anom === 1 ? '<div style="color: #F59E0B; font-weight: bold; margin-top: 4px;">⚠️ ANOMALY EVENT DETECTED</div>' : ''}
          </div>
        `
      }
    },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '45', right: '20', top: '15', height: '56%' },
      { left: '45', right: '20', top: '77%', height: '15%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: timestamps,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#24324A' } },
        axisLabel: { show: false },
        splitLine: { show: true, lineStyle: { color: '#141D2C', type: 'dashed' } }
      },
      {
        gridIndex: 1,
        type: 'category',
        data: timestamps,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#24324A' } },
        axisLabel: { color: '#94A3B8', fontSize: 10, fontFamily: 'Fira Code' },
        splitLine: { show: true, lineStyle: { color: '#141D2C', type: 'dashed' } }
      }
    ],
    yAxis: [
      {
        type: 'value',
        name: 'kWh',
        nameTextStyle: { color: '#94A3B8', fontSize: 10 },
        axisLine: { show: false },
        axisLabel: { color: '#94A3B8', fontSize: 10, fontFamily: 'Fira Code' },
        splitLine: { lineStyle: { color: '#141D2C' } }
      },
      {
        gridIndex: 1,
        type: 'value',
        name: 'Δ kWh',
        nameTextStyle: { color: '#94A3B8', fontSize: 9 },
        axisLine: { show: false },
        axisLabel: { color: '#94A3B8', fontSize: 9, fontFamily: 'Fira Code' },
        splitLine: { lineStyle: { color: '#141D2C' } }
      }
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: [0, 1],
        start: 0,
        end: 25
      },
      {
        type: 'slider',
        xAxisIndex: [0, 1],
        bottom: 2,
        height: 16,
        borderColor: '#1E293B',
        backgroundColor: '#0F1622',
        fillerColor: 'rgba(59, 130, 246, 0.15)',
        handleStyle: { color: '#3B82F6' },
        textStyle: { color: 'transparent' },
        start: 0,
        end: 25
      }
    ],
    series: [
      {
        name: 'Actual Energy',
        type: 'line',
        data: actuals,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#EF4444' }
      },
      {
        name: 'Expected Baseline',
        type: 'line',
        data: expecteds,
        showSymbol: false,
        lineStyle: { width: 1.5, color: '#3B82F6', type: 'dashed' }
      },
      {
        name: 'Anomaly Markers',
        type: 'scatter',
        data: anomalies,
        symbol: 'diamond',
        symbolSize: 8,
        itemStyle: { color: '#F59E0B', borderColor: '#FFF', borderWidth: 1 }
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
            return val > 15 ? '#EF4444' : val > 0 ? '#F59E0B' : '#10B981'
          }
        }
      }
    ]
  }
})
</script>
