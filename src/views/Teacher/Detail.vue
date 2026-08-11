<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <el-button link type="primary" @click="$router.back()">返回</el-button>
      <h2>{{ detail?.name || '教师详情' }}</h2>
    </div>

    <template v-if="detail">
      <el-card>
        <p><b>职称：</b>{{ detail.title }}</p>
        <p><b>手机：</b>{{ detail.phone }}</p>
        <p><b>邮箱：</b>{{ detail.email }}</p>
        <p><b>负责课程：</b>{{ detail.courseCount }}</p>
        <p><b>学生人数：</b>{{ detail.studentCount }}</p>
        <p><b>平均完成率：</b>{{ detail.avgCompletion }}%</p>
      </el-card>

      <el-card style="margin-top: 16px">
        <template #header>负责课程</template>
        <el-table :data="detail.courses || []" border>
          <el-table-column prop="name" label="课程名称" />
          <el-table-column prop="studentCount" label="学生数" width="120" />
          <el-table-column prop="completionRate" label="完成率(%)" width="120" />
        </el-table>
      </el-card>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getTeacherDetail } from '@/api/teacher'

const route = useRoute()
const loading = ref(false)
const detail = ref(null)

async function loadDetail() {
  loading.value = true
  try {
    const res = await getTeacherDetail(route.params.id)
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
