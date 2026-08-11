<script setup>


import {
onMounted,
ref
}
from 'vue'


import * as echarts from 'echarts'



const chartRef=ref()



onMounted(()=>{


const chart =
echarts.init(chartRef.value)



chart.setOption({


title:{
text:'课程分类'
},



series:[

{

type:'pie',


data:[

{
name:'AI课程',
value:40
},

{
name:'前端课程',
value:30
},

{
name:'算法课程',
value:30
}


]

}


]


})


})


</script>

<template>


<div
ref="chartRef"
class="chart"
>


</div>


</template>
