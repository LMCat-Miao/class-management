<template>
  <div class="panel">
    <el-form label-width="96px" class="form">
      <el-form-item label="关联课程">
        <el-input
          v-model="courseName"
          placeholder="可选，填写后解析结果更贴近课程"
          clearable
        />
      </el-form-item>
      <el-form-item label="PDF 文件" required>
        <input type="file" accept=".pdf,application/pdf" @change="onFileChange" />
        <div v-if="fileName" class="file-name">已选择：{{ fileName }}</div>
      </el-form-item>
      <el-form-item v-if="parsing" label="解析进度">
        <el-progress :percentage="progress" />
      </el-form-item>
      <el-form-item>
        <el-button
          v-permission="'ai:parse'"
          type="primary"
          :loading="parsing"
          @click="handleParse"
        >
          开始解析
        </el-button>
      </el-form-item>
    </el-form>

    <div class="result" v-loading="parsing && progress >= 100">
      <template v-if="result">
        <el-card shadow="never">
          <template #header>课程摘要</template>
          <p>{{ result.summary }}</p>
        </el-card>

        <el-card shadow="never" style="margin-top: 12px">
          <template #header>核心知识点</template>
          <el-tag
            v-for="item in result.knowledgePoints"
            :key="item"
            style="margin: 0 8px 8px 0"
          >
            {{ item }}
          </el-tag>
        </el-card>

        <el-card shadow="never" style="margin-top: 12px">
          <template #header>章节结构</template>
          <el-timeline>
            <el-timeline-item
              v-for="(item, index) in result.chapters"
              :key="index"
            >
              {{ item }}
            </el-timeline-item>
          </el-timeline>
        </el-card>

        <el-row :gutter="12" style="margin-top: 12px">
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>学习重点</template>
              <ul>
                <li v-for="item in result.focus" :key="item">{{ item }}</li>
              </ul>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card shadow="never">
              <template #header>学习难点</template>
              <ul>
                <li v-for="item in result.difficulties" :key="item">{{ item }}</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </template>
      <el-empty v-else description="上传 PDF 后开始 AI 解析" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { parsePdf } from '@/api/ai'

const courseName = ref('')
const selectedFile = ref(null)
const fileName = ref('')
const parsing = ref(false)
const progress = ref(0)
const result = ref(null)

function onFileChange(event) {
  const file = event.target.files?.[0]
  selectedFile.value = file || null
  fileName.value = file?.name || ''
  result.value = null
}

async function handleParse() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择 PDF 文件')
    return
  }
  if (!/\.pdf$/i.test(selectedFile.value.name)) {
    ElMessage.warning('仅支持 PDF 文件')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  if (courseName.value.trim()) {
    formData.append('courseName', courseName.value.trim())
  }

  parsing.value = true
  progress.value = 0
  result.value = null
  try {
    const res = await parsePdf(formData, (percent) => {
      progress.value = percent
    })
    result.value = res.data
    ElMessage.success('解析完成')
  } catch (error) {
    ElMessage.error(error.message || '解析失败')
  } finally {
    parsing.value = false
  }
}
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

.file-name {
  margin-top: 8px;
  color: #909399;
  font-size: 13px;
}

ul {
  margin: 0;
  padding-left: 18px;
  line-height: 1.8;
}

p {
  margin: 0;
  line-height: 1.7;
}

@media (max-width: 900px) {
  .panel {
    grid-template-columns: 1fr;
  }
}
</style>
