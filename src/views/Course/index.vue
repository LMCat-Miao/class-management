<template>
    <div class="crouse">
        <h2>课程管理</h2>
        <el-from :model="queryParams" inline>
            <el-form-item label="课程名称">
                <el-input v-model ="queryParams.name" palceholder="请输入课程名称" clearable/>
            </el-form-item>

            <el-form-item label="课程分类">
                <el-select v-model="queryParams.category" placeholder="请选择分类" clearable>
                    <el-option label="前端" value="fronted"/>
                    <el-option label="人工智能" value="ai"/>
                    <el-option label="算法" value="algorithm"/>
                </el-select>
            </el-form-item>

            <el-from-item label="状态">
                <el-select v-model="queryParams.status" placeholder="请选择状态" clearable>
                    <el-option label="正常" value="1"/>
                    <el-option label="停用" value="0"/>
                </el-select>    
            </el-from-item>

            <el-from-item>
                <el-button type="primary" @click="handelSearch">搜索</el-button>
                <el-button @click="handelReset">重置</el-button>
            </el-from-item>
        </el-from>
    </div>
</template>

<script setup>
import { reactive,ref,onMounted } from 'vue'
import {getCourseList} from '@/api/course'

const courseList = ref([])
const total = ref(0)
const loading = ref(false)
// 定义查询参数对象
const queryParams = reactive({
    name: '',
    category: '',
    status: '',
    page: 1,
    pageSize: 10
})
// 获取课程列表
const getList = async()=>{
    loading.value=true
    try {const res = await getCourseList(queryParams)
    courseList.value = res.data.list
    total.value = res.data.total
} finally{
    loading.value=false
}
}
const handelSearch = ()=>{
    queryParams.page=1
    getList()
}

const handelReset = ()=>{
    queryParams.name=''
    queryParams.category=''
    queryParams.status=''
    queryParams.page=1
    getList()
}
</script>