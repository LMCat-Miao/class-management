<template>
  <div class="panel">
    <el-form :model="form" label-width="96px" class="form">
      <el-form-item label="课程名称" required>
        <el-input v-model="form.name" placeholder="例如：Vue3企业级开发" clearable />
      </el-form-item>
      <el-form-item label="关键词">
        <el-select
          v-model="form.keywords"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="输入后回车添加，如 Vue3、Pinia"
          style="width: 100%"
        />
      </el-form-item>
      <el-form-item label="课程分类">
        <el-select v-model="form.category" clearable placeholder="可选" style="width: 100%">
          <el-option v-for="item in categories" :key="item" :label="item" :value="item" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button
          v-permission="'ai:intro'"
          type="primary"
          :loading="loading"
          @click="handleGenerate"
        >
          AI 生成课程简介
        </el-button>
        <el-button :disabled="!form.intro" @click="handleGenerate">重新生成</el-button>
      </el-form-item>
    </el-form>

    <div class="result">
      <div class="result-header">
        <h3>生成结果</h3>
        <div>
          <el-button :disabled="!form.intro" @click="copyIntro">复制</el-button>
          <el-button
            type="success"
            :disabled="!form.intro"
            @click="applyToCourse"
          >
            应用到课程
          </el-button>
        </div>
      </div>
      <el-input
        v-model="form.intro"
        type="textarea"
        :rows="8"
        placeholder="生成的课程简介将显示在这里，可继续编辑"
      />
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { generateIntro } from '@/api/ai'
import { AI_INTRO_DRAFT_KEY } from '@/constants/ai'

const router = useRouter()
const loading = ref(false)
const categories = ['前端', 'AI', 'Python', '算法', 'Java']

const form = reactive({
  name: '',
  keywords: ['Vue3', 'Pinia', 'Router'],
  category: '前端',
  intro: ''
})

async function handleGenerate() {
  if (!form.name.trim()) {
    ElMessage.warning('请先填写课程名称')
    return
  }
  loading.value = true
  try {
    const res = await generateIntro({
      name: form.name,
      keywords: form.keywords,
      category: form.category
    })
    form.intro = res.data.intro
    ElMessage.success('生成成功')
  } catch (error) {
    ElMessage.error(error.message || '生成失败')
  } finally {
    loading.value = false
  }
}

async function copyIntro() {
  try {
    await navigator.clipboard.writeText(form.intro)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败')
  }
}

function applyToCourse() {
  sessionStorage.setItem(
    AI_INTRO_DRAFT_KEY,
    JSON.stringify({
      name: form.name,
      category: form.category,
      intro: form.intro,
      keywords: form.keywords
    })
  )
  ElMessage.success('已准备应用到课程，正在跳转…')
  router.push({ path: '/course', query: { openCreate: '1' } })
}

</script>

<style scoped>
.panel {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.form {
  background: #fafafa;
  padding: 16px;
  border-radius: 4px;
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.result-header h3 {
  margin: 0;
  font-size: 16px;
}

@media (max-width: 900px) {
  .panel {
    grid-template-columns: 1fr;
  }
}
</style>
