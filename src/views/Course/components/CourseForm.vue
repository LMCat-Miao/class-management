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
        <el-input
          v-model="form.intro"
          type="textarea"
          :rows="4"
          placeholder="请输入课程简介"
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="submit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { reactive, ref, watch } from 'vue'
import { createCourse, updateCourse } from '@/api/course'
import { getTeacherList } from '@/api/teacher'
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
    }
  }
)

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
