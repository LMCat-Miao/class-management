<template>
  <el-dialog
    :model-value="modelValue"
    :title="isEdit ? '编辑学生' : '新增学生'"
    width="560px"
    destroy-on-close
    @close="emit('update:modelValue', false)"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="88px">
      <el-form-item label="姓名" prop="name">
        <el-input v-model="form.name" />
      </el-form-item>
      <el-form-item label="学号" prop="studentNo">
        <el-input v-model="form.studentNo" />
      </el-form-item>
      <el-form-item label="班级" prop="className">
        <el-input v-model="form.className" />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="form.phone" />
      </el-form-item>
      <el-form-item label="状态" prop="status">
        <el-radio-group v-model="form.status">
          <el-radio :value="1">正常</el-radio>
          <el-radio :value="0">停用</el-radio>
        </el-radio-group>
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
import { ElMessage } from 'element-plus'
import { createStudent, updateStudent } from '@/api/student'

const props = defineProps({
  modelValue: Boolean,
  student: { type: Object, default: null }
})
const emit = defineEmits(['update:modelValue', 'success'])

const formRef = ref()
const submitting = ref(false)
const isEdit = ref(false)
const form = reactive({
  name: '',
  studentNo: '',
  className: '',
  phone: '',
  status: 1
})
const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  studentNo: [{ required: true, message: '请输入学号', trigger: 'blur' }]
}

watch(
  () => props.modelValue,
  (visible) => {
    if (!visible) return
    if (props.student) {
      isEdit.value = true
      Object.assign(form, {
        name: props.student.name,
        studentNo: props.student.studentNo,
        className: props.student.className,
        phone: props.student.phone,
        status: props.student.status
      })
    } else {
      isEdit.value = false
      Object.assign(form, {
        name: '',
        studentNo: '',
        className: '',
        phone: '',
        status: 1
      })
    }
  }
)

async function submit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    if (isEdit.value) {
      await updateStudent(props.student.id, { ...form })
      ElMessage.success('更新成功')
    } else {
      await createStudent({ ...form })
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
