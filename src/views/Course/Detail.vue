<template>
  <div class="page" v-loading="loading">
    <div class="page-header">
      <div>
        <el-button link type="primary" @click="$router.back()">返回</el-button>
        <h2>{{ detail?.name || '课程详情' }}</h2>
      </div>
    </div>

    <el-row :gutter="16" v-if="detail">
      <el-col :span="16">
        <el-card>
          <template #header>基本信息</template>
          <div class="basic">
            <el-image :src="detail.cover" style="width: 180px; height: 100px" fit="cover" />
            <div class="basic-info">
              <p><b>分类：</b>{{ detail.category }}</p>
              <p><b>教师：</b>{{ detail.teacher }}</p>
              <p><b>难度：</b>{{ detail.difficulty }}</p>
              <p><b>时长：</b>{{ detail.duration }} 小时</p>
              <p><b>学生：</b>{{ detail.studentCount }} 人</p>
              <p><b>完成率：</b>{{ detail.completionRate }}%</p>
              <p><b>简介：</b>{{ detail.intro }}</p>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>课程章节</template>
          <el-timeline>
            <el-timeline-item
              v-for="item in detail.chapters || []"
              :key="item.id"
            >
              {{ item.title }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card>
          <template #header>学习数据</template>
          <p>学习人数：{{ detail.learnCount }}</p>
          <p>学生数量：{{ detail.studentCount }}</p>
          <p>完成率：{{ detail.completionRate }}%</p>
        </el-card>

        <el-card style="margin-top: 16px">
          <template #header>教学资源</template>
          <el-empty v-if="!detail.resources?.length" description="暂无资源" />
          <ul v-else class="resource-list">
            <li v-for="item in detail.resources" :key="item.id">
              {{ item.name }}（{{ item.type }}）
            </li>
          </ul>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getCourseDetail } from '@/api/course'

const route = useRoute()
const loading = ref(false)
const detail = ref(null)

async function loadDetail() {
  loading.value = true
  try {
    const res = await getCourseDetail(route.params.id)
    detail.value = res.data
  } catch (error) {
    ElMessage.error(error.message || '加载详情失败')
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

.basic {
  display: flex;
  gap: 16px;
}

.basic-info p {
  margin: 6px 0;
}

.resource-list {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}
</style>
