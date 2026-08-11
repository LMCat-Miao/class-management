<template>
  <div class="dashboard">
    <DataCard />
    <div class="chart-container">
      <LineChart />
    </div>
    <div class="chart-row">
      <PieChart />
      <BarChart />
    </div>
  </div>
</template>

<script setup>
import DataCard from './DataCard.vue'
import LineChart from './LineChart.vue'
import PieChart from './PieChart.vue'
import BarChart from './BarChart.vue'
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.chart-container,
.chart-row > * {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 900px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
}
</style>
