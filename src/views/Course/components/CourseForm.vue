<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑课程' : '新增课程'"
    width="640px"
    destroy-on-close
    @close="emit('update:modelValue', false)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
      <el-form-item label="课程名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入课程名称" />
      </el-form-item>
      <el-form-item label="课程封面" prop="cover">
        <el-input v-model="form.cover" placeholder="封面图片 URL" />
      </el-form-item>
      <el-form-item label="课程分类" prop="category">
        <el-select v-model="form.category" placeholder="请选择分类" style="width: 100%">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item label="授课教师" prop="teacherId">
        <el-select v-model="form.teacherId" placeholder="请选择教师" style="width: 100%">
          <el-option
            v-for="item in teachers"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="课程难度" prop="difficulty">
        <el-select v-model="form.difficulty" placeholder="请选择难度" style="width: 100%">
          <el-option label="初级" value="初级" />
          <el-option label="中级" value="中级" />
          <el-option label="高级" value="高级" />
        </el-select>
      </el-form-item>
      <el-form-item label="课程时长" prop="duration">
        <el-input-number v-model="form.duration" :min="1" :max="200" />
        <span style="margin-left: 8px">小时</span>
      </el-form-item>
      <el-form-item label="课程状态" prop="status">
        <el-radio-group v-model="form.status">
          <el-radio :value="1">上架</el-radio>
          <el-radio :value="0">下架</el-radio>
        </el-radio-group>
      </el-form-item>
      <el-form-item label="课程简介" prop="intro">
        <div class="intro-box">
          <el-input
            v-model="form.intro"
            type="textarea"
            :rows="4"
            placeholder="请输入课程简介"
          />
          <el-button
            v-permission="'ai:intro'"
            class="ai-btn"
            type="primary"
            plain
            :loading="aiLoading"
            @click="openAiDialog"
          >
            AI 生成课程简介
          </el-button>
        </div>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="aiVisible" title="AI 生成课程简介" width="480px" append-to-body>
    <el-form label-width="80px">
      <el-form-item label="关键词">
        <el-select
          v-model="aiKeywords"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入后回车添加"
          style="width: 100%"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="aiVisible = false">取消</el-button>
      <el-button type="primary" :loading="aiLoading" @click="handleAiGenerate">
        开始生成
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { createCourse, updateCourse } from '@/api/course'
import { getTeacherList } from '@/api/teacher'
import { generateIntro } from '@/api/ai'
import { AI_INTRO_DRAFT_KEY } from '@/constants/ai'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: Boolean,
  course: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)
const aiLoading = ref(false)
const aiVisible = ref(false)
const aiKeywords = ref([])
const teachers = ref([])
const categories = ['前端', 'AI', 'Python', '算法', 'Java']
const isEdit = ref(false)

const form = reactive({
  name: '',
  cover: '',
  category: '',
  teacherId: undefined,
  difficulty: '中级',
  duration: 24,
  status: 1,
  intro: ''
})

const rules = {
  name: [{ required: true, message: '请输入课程名称', trigger: 'blur' }],
  category: [{ required: true, message: '请选择分类', trigger: 'change' }],
  teacherId: [{ required: true, message: '请选择教师', trigger: 'change' }]
}

function resetForm() {
  Object.assign(form, {
    name: '',
    cover: '',
    category: '',
    teacherId: undefined,
    difficulty: '中级',
    duration: 24,
    status: 1,
    intro: ''
  })
}

function applyAiDraft() {
  const raw = sessionStorage.getItem(AI_INTRO_DRAFT_KEY)
  if (!raw) return
  try {
    const draft = JSON.parse(raw)
    if (draft.name) form.name = draft.name
    if (draft.category) form.category = draft.category
    if (draft.intro) form.intro = draft.intro
    sessionStorage.removeItem(AI_INTRO_DRAFT_KEY)
    ElMessage.success('已填入 AI 生成的课程简介')
  } catch {
    sessionStorage.removeItem(AI_INTRO_DRAFT_KEY)
  }
}

watch(
  () => props.modelValue,
  async (visible) => {
    if (!visible) return
    const res = await getTeacherList({ page: 1, pageSize: 100 })
    teachers.value = res.data.list || []
    if (props.course) {
      isEdit.value = true
      Object.assign(form, {
        name: props.course.name,
        cover: props.course.cover,
        category: props.course.category,
        teacherId: props.course.teacherId,
        difficulty: props.course.difficulty,
        duration: props.course.duration,
        status: props.course.status,
        intro: props.course.intro
      })
    } else {
      isEdit.value = false
      resetForm()
      applyAiDraft()
    }
  }
)

function openAiDialog() {
  if (!form.name.trim()) {
    ElMessage.warning('请先填写课程名称')
    return
  }
  aiKeywords.value = form.category ? [form.category] : []
  aiVisible.value = true
}

async function handleAiGenerate() {
  aiLoading.value = true
  try {
    const res = await generateIntro({
      name: form.name,
      keywords: aiKeywords.value,
      category: form.category
    })
    form.intro = res.data.intro
    aiVisible.value = false
    ElMessage.success('简介已生成')
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    aiLoading.value = false
  }
}

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateCourse(props.course.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createCourse({ ...form })
      ElMessage.success('创建成功')
    }
    emit('update:modelValue', false)
    emit('success')
  } catch (error) {
    ElMessage.error(error.message || '保存失败')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.intro-box {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ai-btn {
  align-self: flex-start;
}
</style>
