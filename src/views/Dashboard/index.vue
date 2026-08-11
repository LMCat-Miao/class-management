<template>


<div class="dashboard">


<DataCard/>


<div class="chart-container">


<LineChart/>


</div>



<div class="chart-row">


<PieChart/>


<BarChart/>


</div>


</div>


</template>



<script setup>


import DataCard from './components/DataCard.vue'


import LineChart from './components/LineChart.vue'


import PieChart from './components/PieChart.vue'


import BarChart from './components/BarChart.vue'


</script>
