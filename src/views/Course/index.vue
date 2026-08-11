<template>
  <div class="course">
    <h2>课程管理</h2>
    <el-form :model="queryParams" inline>
      <el-form-item label="课程名称">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入课程名称"
          clearable
        />
      </el-form-item>

      <el-form-item label="课程分类">
        <el-select
          v-model="queryParams.category"
          placeholder="请选择分类"
          clearable
        >
          <el-option label="前端" value="frontend" />
          <el-option label="人工智能" value="ai" />
          <el-option label="算法" value="algorithm" />
        </el-select>
      </el-form-item>

      <el-form-item label="状态">
        <el-select
          v-model="queryParams.status"
          placeholder="请选择状态"
          clearable
        >
          <el-option label="正常" value="1" />
          <el-option label="停用" value="0" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <BaseTable
      :data="courseList"
      :columns="columns"
      :loading="loading"
    />

    <div class="pagination">
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @size-change="getList"
        @current-change="getList"
      />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getCourseList } from '@/api/course'
import BaseTable from '@/components/BaseTable.vue'

const courseList = ref([])
const total = ref(0)
const loading = ref(false)

const queryParams = reactive({
  name: '',
  category: '',
  status: '',
  page: 1,
  pageSize: 10
})

const columns = [
  { prop: 'name', label: '课程名称' },
  { prop: 'category', label: '分类' },
  { prop: 'status', label: '状态' },
  { prop: 'teacher', label: '教师' }
]

const getList = async () => {
  loading.value = true
  try {
    const res = await getCourseList(queryParams)
    courseList.value = res.data?.list || []
    total.value = res.data?.total || 0
  } catch (error) {
    ElMessage.error(error.message || '获取课程列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  getList()
}

const handleReset = () => {
  queryParams.name = ''
  queryParams.category = ''
  queryParams.status = ''
  queryParams.page = 1
  getList()
}

onMounted(() => {
  getList()
})
</script>

<style scoped>
.course {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.course h2 {
  margin: 0 0 16px;
  font-size: 18px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
