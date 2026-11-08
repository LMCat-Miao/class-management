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

      <!-- 选课管理：仅管理员可见；后端仍强制 admin-only -->
      <el-card v-if="isAdmin" style="margin-top: 16px">
        <template #header>
          <div class="enroll-header">
            <span>选课管理</span>
            <el-button type="primary" size="small" :loading="enrollLoading" @click="openAssign">
              分配课程
            </el-button>
          </div>
        </template>

        <el-table v-loading="enrollLoading" :data="enrollments" stripe empty-text="暂无选课记录">
          <el-table-column prop="courseName" label="课程" min-width="160" />
          <el-table-column prop="courseId" label="课程ID" width="90" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.status === 1 ? 'success' : 'info'" size="small">
                {{ row.status === 1 ? '在读' : '已退选' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="enrolledAt" label="选课时间" width="170" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 1"
                link
                type="danger"
                :disabled="droppingId === row.id"
                @click="handleDrop(row)"
              >
                退选
              </el-button>
              <el-button
                v-else
                link
                type="primary"
                :disabled="assigning"
                @click="handleReEnroll(row)"
              >
                恢复
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </template>

    <el-dialog v-model="assignVisible" title="分配课程" width="480px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="课程" required>
          <el-select
            v-model="assignCourseId"
            filterable
            clearable
            placeholder="请选择课程"
            style="width: 100%"
            :loading="courseLoading"
          >
            <el-option
              v-for="c in courseOptions"
              :key="c.id"
              :label="`${c.name} (#${c.id})`"
              :value="c.id"
              :disabled="activeCourseIds.has(c.id)"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="assignVisible = false">取消</el-button>
        <el-button type="primary" :loading="assigning" @click="confirmAssign">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { ROLES } from '@/constants/roles'
import { getStudentDetail } from '@/api/student'
import { getCourseList } from '@/api/course'
import {
  createEnrollment,
  dropEnrollment,
  getEnrollmentsByStudent
} from '@/api/enrollment'

const route = useRoute()
const userStore = useUserStore()
const isAdmin = computed(() => userStore.roles.includes(ROLES.ADMIN))

const loading = ref(false)
const detail = ref(null)

const enrollLoading = ref(false)
const enrollments = ref([])
const droppingId = ref(null)

const assignVisible = ref(false)
const assignCourseId = ref(undefined)
const assigning = ref(false)
const courseLoading = ref(false)
const courseOptions = ref([])

const activeCourseIds = computed(() => {
  const ids = new Set()
  for (const row of enrollments.value) {
    if (row.status === 1) ids.add(row.courseId)
  }
  return ids
})

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

async function loadEnrollments() {
  if (!isAdmin.value) return
  enrollLoading.value = true
  try {
    const res = await getEnrollmentsByStudent(route.params.id)
    enrollments.value = Array.isArray(res.data) ? res.data : []
  } catch (error) {
    ElMessage.error(error.message || '加载选课失败')
  } finally {
    enrollLoading.value = false
  }
}

async function openAssign() {
  assignCourseId.value = undefined
  assignVisible.value = true
  courseLoading.value = true
  try {
    const res = await getCourseList({ page: 1, pageSize: 200 })
    courseOptions.value = res.data?.list || []
  } catch (error) {
    ElMessage.error(error.message || '加载课程失败')
  } finally {
    courseLoading.value = false
  }
}

async function confirmAssign() {
  if (!assignCourseId.value) {
    ElMessage.warning('请选择课程')
    return
  }
  assigning.value = true
  try {
    await createEnrollment({
      studentId: Number(route.params.id),
      courseId: Number(assignCourseId.value)
    })
    ElMessage.success('选课成功')
    assignVisible.value = false
    await loadEnrollments()
  } catch (error) {
    ElMessage.error(error.message || '选课失败')
  } finally {
    assigning.value = false
  }
}

async function handleDrop(row) {
  await ElMessageBox.confirm(`确认退选「${row.courseName || row.courseId}」？`, '提示', {
    type: 'warning'
  })
  droppingId.value = row.id
  try {
    await dropEnrollment(row.id)
    ElMessage.success('已退选')
    await loadEnrollments()
  } catch (error) {
    ElMessage.error(error.message || '退选失败')
  } finally {
    droppingId.value = null
  }
}

/** 对已退选记录再次选课：走创建接口，后端恢复 status=1 */
async function handleReEnroll(row) {
  assigning.value = true
  try {
    await createEnrollment({
      studentId: Number(route.params.id),
      courseId: Number(row.courseId)
    })
    ElMessage.success('已恢复选课')
    await loadEnrollments()
  } catch (error) {
    ElMessage.error(error.message || '恢复失败')
  } finally {
    assigning.value = false
  }
}

onMounted(async () => {
  await loadDetail()
  await loadEnrollments()
})
</script>

<style scoped>
.page-header h2 {
  display: inline;
  margin-left: 8px;
}
p {
  margin: 8px 0;
}
.enroll-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
