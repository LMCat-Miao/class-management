<template>
  <div class="cards">
    <el-card>
      <h3>课程数量</h3>
      <p>500</p>
    </el-card>
    <el-card>
      <h3>教师数量</h3>
      <p>80</p>
    </el-card>
    <el-card>
      <h3>学生数量</h3>
      <p>12000</p>
    </el-card>
  </div>
</template>

<style scoped>
.cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.cards h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #909399;
}

.cards p {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

@media (max-width: 900px) {
  .cards {
    grid-template-columns: 1fr;
  }
}
</style>
