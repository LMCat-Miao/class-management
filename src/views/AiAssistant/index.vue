<template>
  <div class="page">
    <div class="page-header">
      <h2>AI 课程助手</h2>
      <p class="desc">把 AI 能力融入课程业务：生成简介、解析资料、产出练习题</p>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane label="生成课程简介" name="intro">
        <IntroGenerator />
      </el-tab-pane>
      <el-tab-pane label="解析课程 PDF" name="pdf">
        <PdfParser />
      </el-tab-pane>
      <el-tab-pane label="生成练习题" name="quiz">
        <QuizGenerator />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import IntroGenerator from './components/IntroGenerator.vue'
import PdfParser from './components/PdfParser.vue'
import QuizGenerator from './components/QuizGenerator.vue'

const activeTab = ref('intro')
</script>

<style scoped>
.page {
  background: #fff;
  padding: 16px;
  border-radius: 4px;
}

.page-header {
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0 0 6px;
  font-size: 18px;
}

.desc {
  margin: 0;
  color: #909399;
  font-size: 13px;
}
</style>
