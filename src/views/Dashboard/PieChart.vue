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
    title: { text: '课程分类' },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: [
          { name: 'AI课程', value: 40 },
          { name: '前端课程', value: 30 },
          { name: '算法课程', value: 30 }
        ]
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
