<template>
  <div class="dashboard" v-loading="loading">
    <section class="welcome">
      <div class="welcome-copy">
        <h2>欢迎回来，{{ nickname }}！</h2>
        <p>{{ welcomeDate }} · 今日教学数据一目了然，继续高效管理课程与学员。</p>
      </div>
      <div class="welcome-deco" aria-hidden="true" />
    </section>

    <section class="stat-grid">
      <article
        v-for="item in cardList"
        :key="item.label"
        class="stat-card"
      >
        <div class="stat-icon" :class="item.tone">
          <el-icon :size="22">
            <component :is="item.icon" />
          </el-icon>
        </div>
        <div class="stat-body">
          <div class="stat-label">{{ item.label }}</div>
          <div class="stat-value">{{ item.value }}</div>
        </div>
      </article>
    </section>

    <section class="chart-row primary">
      <el-card class="chart-card trend" shadow="never">
        <div class="chart-head">
          <h3>课程与学生趋势</h3>
          <span class="chart-hint">近 12 个月（含演示趋势数据）</span>
        </div>
        <div ref="trendRef" class="chart chart-lg"></div>
      </el-card>
      <el-card class="chart-card category" shadow="never">
        <div class="chart-head">
          <h3>课程分类占比</h3>
        </div>
        <div ref="categoryRef" class="chart chart-lg"></div>
      </el-card>
    </section>

    <section class="chart-row secondary">
      <el-card class="chart-card" shadow="never">
        <div class="chart-head">
          <h3>热门课程排行</h3>
          <span class="chart-hint">按学习人数</span>
        </div>
        <div ref="hotRef" class="chart"></div>
      </el-card>
      <el-card class="chart-card" shadow="never">
        <div class="chart-head">
          <h3>课程平均完成率</h3>
        </div>
        <div ref="completionRef" class="chart"></div>
      </el-card>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  Reading,
  Avatar,
  User,
  DataLine
} from '@element-plus/icons-vue'
import { getDashboardData } from '@/api/dashboard'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const data = ref(null)

const trendRef = ref()
const categoryRef = ref()
const hotRef = ref()
const completionRef = ref()

/** @type {import('echarts').ECharts[]} */
const charts = []

const nickname = computed(() => userStore.nickname || '用户')

const welcomeDate = computed(() => {
  const now = new Date()
  const week = ['日', '一', '二', '三', '四', '五', '六'][now.getDay()]
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  return `${y}年${m}月${d}日 星期${week}`
})

const cardList = computed(() => {
  const cards = data.value?.cards || {}
  const dash = (v) => (v === undefined || v === null ? '—' : v)
  return [
    {
      label: '课程总数',
      value: dash(cards.courseTotal),
      icon: Reading,
      tone: 'tone-blue'
    },
    {
      label: '教师总数',
      value: dash(cards.teacherTotal),
      icon: Avatar,
      tone: 'tone-cyan'
    },
    {
      label: '学生总数',
      value: dash(cards.studentTotal),
      icon: User,
      tone: 'tone-violet'
    },
    {
      label: '累计学习人数',
      value: dash(cards.learnTotal),
      icon: DataLine,
      tone: 'tone-teal'
    }
  ]
})

function disposeCharts() {
  while (charts.length) {
    const chart = charts.pop()
    chart?.dispose()
  }
}

function createChart(el, option) {
  if (!el) return null
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
  return chart
}

function renderCharts() {
  const d = data.value
  if (!d) return
  disposeCharts()

  createChart(trendRef.value, {
    color: ['#3b5bdb', '#15aabf'],
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['课程数量', '新增学生'],
      top: 0,
      right: 0,
      textStyle: { color: '#64748b', fontSize: 12 }
    },
    grid: { left: 48, right: 20, top: 40, bottom: 36 },
    xAxis: {
      type: 'category',
      data: d.courseTrend?.months || [],
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8' }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        name: '课程数量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: d.courseTrend?.values || []
      },
      {
        name: '新增学生',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        areaStyle: { opacity: 0.08 },
        data: d.studentTrend?.values || []
      }
    ]
  })

  createChart(categoryRef.value, {
    color: ['#3b5bdb', '#748ffc', '#15aabf', '#9775fa', '#51cf66', '#fcc419'],
    tooltip: { trigger: 'item' },
    legend: {
      orient: 'vertical',
      right: 0,
      top: 'middle',
      textStyle: { color: '#64748b', fontSize: 12 }
    },
    series: [
      {
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['38%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
        label: { color: '#64748b', fontSize: 12 },
        data: d.categoryPie || []
      }
    ]
  })

  createChart(hotRef.value, {
    color: ['#3b5bdb'],
    tooltip: { trigger: 'axis' },
    grid: { left: 48, right: 16, top: 24, bottom: 56 },
    xAxis: {
      type: 'category',
      data: (d.hotCourses || []).map((i) => i.name),
      axisLabel: {
        interval: 0,
        rotate: 20,
        color: '#94a3b8',
        fontSize: 11,
        formatter: (val) =>
          String(val).length > 8 ? `${String(val).slice(0, 8)}…` : val
      },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      name: '学习人数',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#94a3b8' }
    },
    series: [
      {
        type: 'bar',
        barMaxWidth: 36,
        itemStyle: {
          borderRadius: [8, 8, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#5c7cfa' },
            { offset: 1, color: '#3b5bdb' }
          ])
        },
        data: (d.hotCourses || []).map((i) => i.value)
      }
    ]
  })

  createChart(completionRef.value, {
    series: [
      {
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        min: 0,
        max: 100,
        progress: {
          show: true,
          width: 14,
          itemStyle: { color: '#3b5bdb' }
        },
        axisLine: {
          lineStyle: { width: 14, color: [[1, '#eef2ff']] }
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        pointer: { show: false },
        anchor: { show: false },
        title: {
          offsetCenter: [0, '68%'],
          color: '#64748b',
          fontSize: 13
        },
        detail: {
          valueAnimation: true,
          formatter: '{value}%',
          offsetCenter: [0, '20%'],
          color: '#1e293b',
          fontSize: 32,
          fontWeight: 700
        },
        data: [{ value: d.completionRate ?? 0, name: '平均完成率' }]
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
  disposeCharts()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1400px;
}

.welcome {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 22px 26px;
  background: linear-gradient(120deg, #edf2ff 0%, #e7f5ff 55%, #f3f0ff 100%);
  border: 1px solid #dbe4ff;
}

.welcome-copy {
  position: relative;
  z-index: 1;
  max-width: 720px;
}

.welcome-copy h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--cm-text);
}

.welcome-copy p {
  margin: 8px 0 0;
  font-size: 13.5px;
  line-height: 1.55;
  color: var(--cm-text-secondary);
}

.welcome-deco {
  position: absolute;
  right: -40px;
  top: -50px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(59, 91, 219, 0.16), transparent 70%);
  pointer-events: none;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 104px;
  padding: 18px 18px;
  background: #fff;
  border: 1px solid var(--cm-border);
  border-radius: 14px;
  box-shadow: var(--cm-shadow-sm);
}

.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.tone-blue {
  background: #edf2ff;
  color: #3b5bdb;
}

.tone-cyan {
  background: #e3fafc;
  color: #0c8599;
}

.tone-violet {
  background: #f3f0ff;
  color: #7048e8;
}

.tone-teal {
  background: #e6fcf5;
  color: #0ca678;
}

.stat-label {
  color: var(--cm-text-secondary);
  font-size: 13px;
  font-weight: 500;
}

.stat-value {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: var(--cm-text);
  line-height: 1.1;
}

.chart-row {
  display: grid;
  gap: 16px;
}

.chart-row.primary {
  grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr);
}

.chart-row.secondary {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
}

.chart-card {
  border: 1px solid var(--cm-border);
  border-radius: 14px;
  background: #fff;
  box-shadow: var(--cm-shadow-sm);
}

.chart-card :deep(.el-card__body) {
  padding: 18px 18px 12px;
}

.chart-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 4px;
}

.chart-head h3 {
  margin: 0;
  font-size: 15px;
  font-weight: 650;
  color: var(--cm-text);
}

.chart-hint {
  font-size: 12px;
  color: var(--cm-text-muted);
  white-space: nowrap;
}

.chart {
  width: 100%;
  height: 320px;
}

.chart-lg {
  height: 340px;
}

@media (max-width: 1200px) {
  .stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-row.primary,
  .chart-row.secondary {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 720px) {
  .stat-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .welcome {
    padding: 18px;
  }

  .welcome-copy h2 {
    font-size: 18px;
  }
}
</style>
