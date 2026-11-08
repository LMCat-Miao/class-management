<template>
  <div class="page">
    <div class="page-header">
      <h2>教学资源</h2>
      <el-button
        v-permission="'resource:upload'"
        type="primary"
        @click="uploadVisible = true"
      >
        上传资源
      </el-button>
    </div>

    <el-form :model="queryParams" inline>
      <el-form-item label="文件名称">
        <el-input v-model="queryParams.name" clearable placeholder="文件名称" />
      </el-form-item>
      <el-form-item label="类型">
        <el-select v-model="queryParams.type" clearable placeholder="类型">
          <el-option
            v-for="item in types"
            :key="item"
            :label="item"
            :value="item"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="所属课程">
        <el-select v-model="queryParams.courseId" clearable placeholder="课程" filterable>
          <el-option
            v-for="item in courseOptions"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="handleReset">重置</el-button>
      </el-form-item>
    </el-form>

    <BaseTable :data="list" :columns="columns" :loading="loading" :action-width="160">
      <template #status="{ row }">
        <el-tag type="success">{{ row.status === 1 ? '正常' : '停用' }}</el-tag>
      </template>
      <template #actions="{ row }">
        <el-button
          v-permission="'resource:view'"
          link
          type="primary"
          :loading="downloadingId === row.id"
          @click="handleDownload(row)"
        >
          下载
        </el-button>
        <el-button
          v-permission="'resource:delete'"
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

    <el-dialog v-model="uploadVisible" title="上传资源" width="520px" destroy-on-close>
      <el-form label-width="88px">
        <el-form-item label="所属课程" required>
          <el-select v-model="uploadForm.courseId" placeholder="请选择课程" style="width: 100%">
            <el-option
              v-for="item in courseOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="选择文件" required>
          <input type="file" @change="onFileChange" />
        </el-form-item>
        <el-form-item v-if="uploading" label="上传进度">
          <el-progress :percentage="progress" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          开始上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseTable from '@/components/BaseTable.vue'
import {
  getResourceList,
  uploadResource,
  deleteResource,
  downloadResource
} from '@/api/resource'
import { getCourseList } from '@/api/course'

const loading = ref(false)
const list = ref([])
const total = ref(0)
const uploadVisible = ref(false)
const uploading = ref(false)
const progress = ref(0)
const downloadingId = ref(null)
const courseOptions = ref([])
const selectedFile = ref(null)
const types = ['PDF', 'PPT', 'Word', 'Excel', '图片', '视频', '其他']

const queryParams = reactive({
  name: '',
  type: '',
  courseId: '',
  page: 1,
  pageSize: 10
})

const uploadForm = reactive({
  courseId: undefined
})

const columns = [
  { prop: 'name', label: '文件名称', minWidth: 180 },
  { prop: 'type', label: '类型', width: 90 },
  { prop: 'courseName', label: '所属课程', minWidth: 140 },
  { prop: 'size', label: '大小', width: 100 },
  { prop: 'uploader', label: '上传人', width: 100 },
  { prop: 'uploadedAt', label: '上传时间', width: 160 },
  { prop: 'status', label: '状态', width: 90, slot: 'status' }
]

async function getList() {
  loading.value = true
  try {
    const res = await getResourceList(queryParams)
    list.value = res.data.list || []
    total.value = res.data.total || 0
  } catch (error) {
    ElMessage.error(error.message || '获取资源失败')
  } finally {
    loading.value = false
  }
}

async function loadCourses() {
  const res = await getCourseList({ page: 1, pageSize: 100 })
  courseOptions.value = res.data.list || []
}

function handleSearch() {
  queryParams.page = 1
  getList()
}

function handleReset() {
  queryParams.name = ''
  queryParams.type = ''
  queryParams.courseId = ''
  queryParams.page = 1
  getList()
}

function onFileChange(event) {
  selectedFile.value = event.target.files?.[0] || null
}

async function handleUpload() {
  if (!uploadForm.courseId) {
    ElMessage.warning('请选择所属课程')
    return
  }
  if (!selectedFile.value) {
    ElMessage.warning('请选择文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('courseId', String(uploadForm.courseId))

  uploading.value = true
  progress.value = 0
  try {
    await uploadResource(formData, (percent) => {
      progress.value = percent
    })
    ElMessage.success('上传成功')
    uploadVisible.value = false
    selectedFile.value = null
    uploadForm.courseId = undefined
    getList()
  } catch (error) {
    ElMessage.error(error.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleDownload(row) {
  downloadingId.value = row.id
  try {
    await downloadResource(row.id)
    ElMessage.success('已开始下载')
  } catch (error) {
    ElMessage.error(error.message || '下载失败')
  } finally {
    downloadingId.value = null
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除资源「${row.name}」？`, '提示', {
    type: 'warning'
  })
  await deleteResource(row.id)
  ElMessage.success('删除成功')
  getList()
}

onMounted(() => {
  getList()
  loadCourses()
})
</script>

<style scoped>
</style>
