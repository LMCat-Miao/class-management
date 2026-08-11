<template>
  <div class="dashboard" v-loading="loading">
    <div class="cards">
      <el-card v-for="item in cardList" :key="item.label">
        <div class="card-label">{{ item.label }}</div>
        <div class="card-value">{{ item.value }}</div>
      </el-card>
    </div>

    <div class="chart-row">
      <el-card class="chart-card">
        <div ref="courseTrendRef" class="chart"></div>
      </el-card>
      <el-card class="chart-card">
        <div ref="studentTrendRef" class="chart"></div>
      </el-card>
    </div>

    <div class="chart-row three">
      <el-card class="chart-card">
        <div ref="categoryRef" class="chart"></div>
      </el-card>
      <el-card class="chart-card">
        <div ref="hotRef" class="chart"></div>
      </el-card>
      <el-card class="chart-card">
        <div ref="completionRef" class="chart"></div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import { getDashboardData } from '@/api/dashboard'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const data = ref(null)

const courseTrendRef = ref()
const studentTrendRef = ref()
const categoryRef = ref()
const hotRef = ref()
const completionRef = ref()

const charts = []

const cardList = computed(() => {
  const cards = data.value?.cards || {}
  return [
    { label: '课程总数', value: cards.courseTotal ?? '-' },
    { label: '教师总数', value: cards.teacherTotal ?? '-' },
    { label: '学生总数', value: cards.studentTotal ?? '-' },
    { label: '累计学习人数', value: cards.learnTotal ?? '-' }
  ]
})

function createChart(el, option) {
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
  return chart
}

function renderCharts() {
  const d = data.value
  if (!d) return

  createChart(courseTrendRef.value, {
    title: { text: '近12个月课程数量变化' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.courseTrend.months },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, data: d.courseTrend.values }]
  })

  createChart(studentTrendRef.value, {
    title: { text: '每月新增学生' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: d.studentTrend.months },
    yAxis: { type: 'value' },
    series: [{ type: 'line', smooth: true, data: d.studentTrend.values, areaStyle: {} }]
  })

  createChart(categoryRef.value, {
    title: { text: '课程分类占比' },
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: '60%',
        data: d.categoryPie
      }
    ]
  })

  createChart(hotRef.value, {
    title: { text: '热门课程排行' },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: d.hotCourses.map((i) => i.name),
      axisLabel: { interval: 0, rotate: 20 }
    },
    yAxis: { type: 'value', name: '学习人数' },
    series: [
      {
        type: 'bar',
        data: d.hotCourses.map((i) => i.value)
      }
    ]
  })

  createChart(completionRef.value, {
    title: { text: '课程平均完成率' },
    series: [
      {
        type: 'gauge',
        progress: { show: true },
        detail: { formatter: '{value}%' },
        data: [{ value: d.completionRate, name: '完成率' }]
      }
    ]
  })
}

function handleResize() {
  charts.forEach((chart) => chart.resize())
}

async function loadData() {
  loading.value = true
  try {
    const res = await getDashboardData()
    data.value = res.data
    requestAnimationFrame(() => renderCharts())
  } catch (error) {
    ElMessage.error(error.message || '加载看板失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  charts.forEach((chart) => chart.dispose())
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.card-label {
  color: #909399;
  font-size: 14px;
}

.card-value {
  margin-top: 8px;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.chart-row.three {
  grid-template-columns: 1fr 1fr 1fr;
}

.chart {
  width: 100%;
  height: 340px;
}

@media (max-width: 1100px) {
  .cards,
  .chart-row,
  .chart-row.three {
    grid-template-columns: 1fr;
  }
}
</style>
