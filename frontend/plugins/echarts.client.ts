import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkLineComponent,
  VisualMapComponent,
  TitleComponent
} from 'echarts/components'
import VChart from 'vue-echarts'

export default defineNuxtPlugin((nuxtApp) => {
  use([
    CanvasRenderer,
    LineChart,
    BarChart,
    ScatterChart,
    GridComponent,
    TooltipComponent,
    LegendComponent,
    DataZoomComponent,
    MarkLineComponent,
    VisualMapComponent,
    TitleComponent
  ])

  nuxtApp.vueApp.component('v-chart', VChart)
})
