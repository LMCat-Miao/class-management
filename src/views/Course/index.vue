<template>
  <div class="page">
    <div class="page-header">
      <h2>课程管理</h2>
      <el-button
        v-permission="'course:add'"
        type="primary"
        @click="openCreate"
      >
        新增课程
      </el-button>
    </div>

    <el-form :model="queryParams" inline class="search-form">
      <el-form-item label="课程名称">
        <el-input v-model="queryParams.name" clearable placeholder="请输入课程名称" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="queryParams.category" clearable placeholder="请选择分类">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="教师">
        <el-input v-model="queryParams.teacher" clearable placeholder="教师姓名" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="queryParams.status" clearable placeholder="状态">
          <el-option label="上架" value="1" />
          <el-option label="下架" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item label="创建时间">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          value-format="YYYY-MM-DD"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <BaseTable
      :data="list"
      :columns="columns"
      :loading="loading"
      :action-width="280"
    >
      <template #cover="{ row }">
        <el-image
          :src="row.cover"
          style="width: 72px; height: 40px"
          fit="cover"
        />
      </template>
      <template #status="{ row }">
        <el-tag :type="row.status === 1 ? 'success' : 'info'">
          {{ row.status === 1 ? '上架' : '下架' }}
        </el-tag>
      </template>
      <template #actions="{ row }">
        <el-button link type="primary" @click="goDetail(row)">查看</el-button>
        <el-button
          v-permission="'course:edit'"
          link
          type="primary"
          @click="openEdit(row)"
        >
          编辑
        </el-button>
        <el-button
          v-permission="'course:publish'"
          link
          type="warning"
          @click="toggleStatus(row)"
        >
          {{ row.status === 1 ? '下架' : '上架' }}
        </el-button>
        <el-button
          v-permission="'course:delete'"
          link
          type="danger"
          @click="handleDelete(row)"
        >
          删除
        </el-button>
      </template>
    </BaseTable>

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

    <CourseForm
      v-model="formVisible"
      :course="current"
      @success="getList"
    />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable from '@/components/BaseTable.vue'
import CourseForm from './components/CourseForm.vue'
import {
  getCourseList,
  deleteCourse,
  updateCourseStatus
} from '@/api/course'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const formVisible = ref(false)
const current = ref(null)
const dateRange = ref([])
const categories = ['前端', 'AI', 'Python', '算法', 'Java']

const queryParams = reactive({
  name: '',
  category: '',
  teacher: '',
  status: '',
  startDate: '',
  endDate: '',
  page: 1,
  pageSize: 10
})

const columns = [
  { prop: 'name', label: '课程名称', minWidth: 160 },
  { prop: 'cover', label: '封面', width: 100, slot: 'cover' },
  { prop: 'category', label: '分类', width: 100 },
  { prop: 'teacher', label: '教师', width: 100 },
  { prop: 'difficulty', label: '难度', width: 80 },
  { prop: 'studentCount', label: '学生数量', width: 100 },
  { prop: 'status', label: '状态', width: 90, slot: 'status' },
  { prop: 'createdAt', label: '创建时间', width: 120 }
]

watch(dateRange, (val) => {
  queryParams.startDate = val?.[0] || ''
  queryParams.endDate = val?.[1] || ''
})

async function getList() {
  loading.value = true
  try {
    const res = await getCourseList(queryParams)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '获取课程失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  queryParams.page = 1
  getList()
}

function handleReset() {
  queryParams.name = ''
  queryParams.category = ''
  queryParams.teacher = ''
  queryParams.status = ''
  queryParams.startDate = ''
  queryParams.endDate = ''
  dateRange.value = []
  queryParams.page = 1
  getList()
}

function openCreate() {
  current.value = null
  formVisible.value = true
}

function openEdit(row) {
  current.value = { ...row }
  formVisible.value = true
}

function goDetail(row) {
  router.push(`/course/${row.id}`)
}

async function toggleStatus(row) {
  const next = row.status === 1 ? 0 : 1
  await updateCourseStatus(row.id, next)
  ElMessage.success(next === 1 ? '已上架' : '已下架')
  getList()
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除课程「${row.name}」？`, '提示', {
    type: 'warning'
  })
  await deleteCourse(row.id)
  ElMessage.success('删除成功')
  getList()
}

onMounted(getList)
</script>

<style scoped>
.page {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.page-header h2 {
  margin: 0;
  font-size: 18px;
}

.search-form {
  margin-bottom: 8px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
