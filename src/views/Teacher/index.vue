<template>
  <div class="page">
    <div class="page-header">
      <h2>教师管理</h2>
      <el-button v-permission="'teacher:add'" type="primary" @click="openCreate">
        新增教师
      </el-button>
    </div>

    <el-form :model="queryParams" inline>
      <el-form-item label="姓名">
        <el-input v-model="queryParams.name" clearable placeholder="教师姓名" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="queryParams.status" clearable placeholder="状态">
          <el-option label="启用" value="1" />
          <el-option label="停用" value="0" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <BaseTable :data="list" :columns="columns" :loading="loading" :action-width="220">
      <template #status="{ row }">
        <el-tag :type="row.status === 1 ? 'success' : 'info'">
          {{ row.status === 1 ? '启用' : '停用' }}
        </el-tag>
      </template>
      <template #actions="{ row }">
        <el-button link type="primary" @click="goDetail(row)">查看</el-button>
        <el-button
          v-permission="'teacher:edit'"
          link
          type="primary"
          @click="openEdit(row)"
        >
          编辑
        </el-button>
        <el-button
          v-permission="'teacher:delete'"
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
        layout="total, sizes, prev, pager, next"
        :page-sizes="[10, 20, 50]"
        @size-change="getList"
        @current-change="getList"
      />
    </div>

    <TeacherForm v-model="formVisible" :teacher="current" @success="getList" />
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable from '@/components/BaseTable.vue'
import TeacherForm from './components/TeacherForm.vue'
import { getTeacherList, deleteTeacher } from '@/api/teacher'

const router = useRouter()
const loading = ref(false)
const list = ref([])
const total = ref(0)
const formVisible = ref(false)
const current = ref(null)

const queryParams = reactive({
  name: '',
  status: '',
  page: 1,
  pageSize: 10
})

const columns = [
  { prop: 'name', label: '姓名' },
  { prop: 'phone', label: '手机号' },
  { prop: 'email', label: '邮箱', minWidth: 160 },
  { prop: 'title', label: '职称' },
  { prop: 'courseCount', label: '负责课程' },
  { prop: 'studentCount', label: '学生数量' },
  { prop: 'status', label: '状态', slot: 'status', width: 90 }
]

async function getList() {
  loading.value = true
  try {
    const res = await getTeacherList(queryParams)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '获取教师列表失败')
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
  router.push(`/teacher/${row.id}`)
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除教师「${row.name}」？`, '提示', {
    type: 'warning'
  })
  await deleteTeacher(row.id)
  ElMessage.success('删除成功')
  getList()
}

onMounted(getList)
</script>

<style scoped>
</style>
