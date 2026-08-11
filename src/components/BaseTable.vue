<template>

    <el-table
        :data="data"
        v-loading="loading"
        border
    >

        <el-table-column
            v-for="column in columns"
            :key="column.prop"
            :prop="column.prop"
            :label="column.label"
        />

    </el-table>

</template>


<script setup>

defineProps({

    data: {
        type: Array,
        default: () => []
    },

    columns: {
        type: Array,
        default: () => []
    },

    loading: {
        type: Boolean,
        default: false
    }

})

</script>