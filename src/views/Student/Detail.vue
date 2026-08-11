<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <el-button link type="primary" @click="$router.back()">返回</el-button>
      <h2>{{ detail?.name || '学生详情' }}</h2>
    </div>

    <template v-if="detail">
      <el-card>
        <p><b>学号：</b>{{ detail.studentNo }}</p>
        <p><b>班级：</b>{{ detail.className }}</p>
        <p><b>手机：</b>{{ detail.phone }}</p>
        <p><b>学习课程：</b>{{ detail.learnCourseCount }}</p>
        <p><b>完成课程：</b>{{ detail.finishCourseCount }}</p>
        <p><b>平均完成率：</b>{{ detail.avgCompletion }}%</p>
        <p><b>注册时间：</b>{{ detail.registeredAt }}</p>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>最近学习</template>
        <el-tag
          v-for="item in detail.recentCourses || []"
          :key="item"
          style="margin-right: 8px; margin-bottom: 8px"
        >
          {{ item }}
        </el-tag>
        <el-empty v-if="!detail.recentCourses?.length" description="暂无学习记录" />
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getStudentDetail } from '@/api/student'

const route = useRoute()
const loading = ref(false)
const detail = ref(null)

async function loadDetail() {
  loading.value = true
  try {
    const res = await getStudentDetail(route.params.id)
    detail.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.page {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}
.page-header h2 {
  display: inline;
  margin-left: 8px;
  font-size: 18px;
}
p {
  margin: 8px 0;
}
</style>
