<template>
  <div class="panel">
    <el-form :model="form" label-width="96px" class="form">
      <el-form-item label="选择课程">
        <el-select
          v-model="form.courseId"
          clearable
          filterable
          placeholder="从已有课程中选择"
          style="width: 100%"
          @change="onCourseChange"
        >
          <el-option
            v-for="item in courses"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="主题">
        <el-input
          v-model="form.topic"
          placeholder="可手输主题，默认使用课程名"
          clearable
        />
      </el-form-item>
      <el-form-item label="题目数量">
        <el-input-number v-model="form.count" :min="1" :max="5" />
      </el-form-item>
      <el-form-item>
        <el-button
          v-permission="'ai:quiz'"
          type="primary"
          :loading="loading"
          @click="handleGenerate"
        >
          AI 生成题目
        </el-button>
        <el-button :disabled="!hasResult" @click="copyAll">复制全部</el-button>
      </el-form-item>
    </el-form>

    <div class="result">
      <template v-if="hasResult">
        <el-card shadow="never">
          <template #header>选择题</template>
          <div v-for="item in quiz.choice" :key="'c' + item.id" class="quiz-item">
            <p class="q">{{ item.id }}. {{ item.question }}</p>
            <p v-for="opt in item.options" :key="opt" class="opt">{{ opt }}</p>
            <p class="ans">答案：{{ item.answer }}</p>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top: 12px">
          <template #header>判断题</template>
          <div v-for="item in quiz.judge" :key="'j' + item.id" class="quiz-item">
            <p class="q">{{ item.id }}. {{ item.question }}</p>
            <p class="ans">答案：{{ item.answer ? '正确' : '错误' }}</p>
          </div>
        </el-card>

        <el-card shadow="never" style="margin-top: 12px">
          <template #header>简答题</template>
          <div v-for="item in quiz.short" :key="'s' + item.id" class="quiz-item">
            <p class="q">{{ item.id }}. {{ item.question }}</p>
            <p class="ans">参考：{{ item.answer }}</p>
          </div>
        </el-card>
      </template>
      <el-empty v-else description="选择课程或输入主题后生成练习题" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getCourseList } from '@/api/course'
import { generateQuiz } from '@/api/ai'

const loading = ref(false)
const courses = ref([])
const quiz = ref({ choice: [], judge: [], short: [] })

const form = reactive({
  courseId: undefined,
  courseName: '',
  topic: '',
  count: 3
})

const hasResult = computed(
  () =>
    quiz.value.choice.length ||
    quiz.value.judge.length ||
    quiz.value.short.length
)

function onCourseChange(id) {
  const course = courses.value.find((item) => item.id === id)
  form.courseName = course?.name || ''
  if (course && !form.topic) {
    form.topic = course.name
  }
}

async function loadCourses() {
  const res = await getCourseList({ page: 1, pageSize: 100 })
  courses.value = res.data.list || []
}

async function handleGenerate() {
  const courseName = form.courseName || form.topic
  if (!courseName.trim()) {
    ElMessage.warning('请选择课程或输入主题')
    return
  }
  loading.value = true
  try {
    const res = await generateQuiz({
      courseName,
      topic: form.topic || courseName,
      count: form.count
    })
    quiz.value = res.data
    ElMessage.success('题目生成成功')
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    loading.value = false
  }
}

function buildText() {
  const lines = []
  lines.push('【选择题】')
  quiz.value.choice.forEach((item) => {
    lines.push(`${item.id}. ${item.question}`)
    item.options.forEach((opt) => lines.push(opt))
    lines.push(`答案：${item.answer}`)
    lines.push('')
  })
  lines.push('【判断题】')
  quiz.value.judge.forEach((item) => {
    lines.push(`${item.id}. ${item.question}`)
    lines.push(`答案：${item.answer ? '正确' : '错误'}`)
    lines.push('')
  })
  lines.push('【简答题】')
  quiz.value.short.forEach((item) => {
    lines.push(`${item.id}. ${item.question}`)
    lines.push(`参考：${item.answer}`)
    lines.push('')
  })
  return lines.join('\n')
}

async function copyAll() {
  try {
    await navigator.clipboard.writeText(buildText())
    ElMessage.success('已复制全部题目')
  } catch {
    ElMessage.error('复制失败')
  }
}

onMounted(loadCourses)
</script>

<style scoped>
.panel {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 24px;
}

.form {
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
  height: fit-content;
}

.quiz-item {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #ebeef5;
}

.quiz-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.q {
  margin: 0 0 6px;
  font-weight: 500;
}

.opt,
.ans {
  margin: 2px 0;
  color: #606266;
  font-size: 13px;
}

.ans {
  color: #67c23a;
}

@media (max-width: 900px) {
  .panel {
    grid-template-columns: 1fr;
  }
}
</style>
