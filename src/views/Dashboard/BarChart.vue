<template>
  <div ref="chartRef" class="chart"></div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref()
let chart = null

onMounted(() => {
  chart = echarts.init(chartRef.value)
  chart.setOption({
    title: { text: '热门课程' },
    xAxis: {
      type: 'category',
      data: ['Vue', 'AI', 'Python']
    },
    yAxis: { type: 'value' },
    series: [
      {
        type: 'bar',
        data: [3000, 5000, 4000]
      }
    ]
  })
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
})

const handleResize = () => {
  chart?.resize()
}
</script>

<style scoped>
.chart {
  width: 100%;
  height: 350px;
}
</style>
