<template>
  <div class="page">
    <div class="page-header">
      <h2>学生管理</h2>
      <el-button v-permission="'student:edit'" type="primary" @click="openCreate">
        新增学生
      </el-button>
    </div>

    <el-form :model="queryParams" inline>
      <el-form-item label="姓名">
        <el-input v-model="queryParams.name" clearable placeholder="学生姓名" />
      </el-form-item>
      <el-form-item label="学号">
        <el-input v-model="queryParams.studentNo" clearable placeholder="学号" />
      </el-form-item>
      <el-form-item label="班级">
        <el-input v-model="queryParams.className" clearable placeholder="班级" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="queryParams.status" clearable placeholder="状态">
          <el-option label="正常" value="1" />
          <el-option label="停用" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <BaseTable :data="list" :columns="columns" :loading="loading" :action-width="240">
      <template #progress="{ row }">
        <el-progress :percentage="row.progress" :stroke-width="10" />
      </template>
      <template #status="{ row }">
        <el-tag :type="row.status === 1 ? 'success' : 'info'">
          {{ row.status === 1 ? '正常' : '停用' }}
        </el-tag>
      </template>
      <template #actions="{ row }">
        <el-button link type="primary" @click="goDetail(row)">查看</el-button>
        <el-button
          v-permission="'student:edit'"
          link
          type="primary"
          @click="openEdit(row)"
        >
          编辑
        </el-button>
        <el-button
          v-permission="'student:status'"
          link
          type="warning"
          @click="toggleStatus(row)"
        >
          {{ row.status === 1 ? '停用' : '启用' }}
        </el-button>
      </template>
    </BaseTable>

    <div class="pagination">
      <el-pagination
        v-model:current-page="queryParams.page"
        v-model:page-size="queryParams.pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next"
        :page-sizes="[10, 20, 50]"
        @size-change="getList"
        @current-change="getList"
      />
    </div>

    <StudentForm v-model="formVisible" :student="current" @success="getList" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import BaseTable from '@/components/BaseTable.vue'
import StudentForm from './components/StudentForm.vue'
import { getStudentList, updateStudentStatus } from '@/api/student'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const formVisible = ref(false)
const current = ref(null)

const queryParams = reactive({
  name: '',
  studentNo: '',
  className: '',
  status: '',
  page: 1,
  pageSize: 10
})

const columns = [
  { prop: 'name', label: '姓名' },
  { prop: 'studentNo', label: '学号' },
  { prop: 'className', label: '班级' },
  { prop: 'phone', label: '手机号' },
  { prop: 'learnCourseCount', label: '学习课程数', width: 110 },
  { prop: 'finishCourseCount', label: '完成课程数', width: 110 },
  { prop: 'progress', label: '学习进度', minWidth: 140, slot: 'progress' },
  { prop: 'status', label: '状态', width: 90, slot: 'status' },
  { prop: 'registeredAt', label: '注册时间', width: 120 }
]

async function getList() {
  loading.value = true
  try {
    const res = await getStudentList(queryParams)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '获取学生列表失败')
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
  queryParams.studentNo = ''
  queryParams.className = ''
  queryParams.status = ''
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
  router.push(`/student/${row.id}`)
}

async function toggleStatus(row) {
  const next = row.status === 1 ? 0 : 1
  await updateStudentStatus(row.id, next)
  ElMessage.success('状态已更新')
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
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
