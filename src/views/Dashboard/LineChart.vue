<template>


<div
ref="chartRef"
class="chart"
>

</div>


</template>



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



const option={


title:{
text:'课程增长趋势'
},



xAxis:{


type:'category',

data:[
'1月',
'2月',
'3月',
'4月'
]


},


yAxis:{


type:'value'


},



series:[


{

data:[
100,
200,
350,
500
],

type:'line'

}


]

}



chart.setOption(option)



})


</script>
