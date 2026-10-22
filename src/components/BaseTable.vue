<template>
  <el-table
    class="cm-table"
    :data="data"
    v-loading="loading"
    :stripe="false"
    :border="false"
  >
    <el-table-column
      v-for="column in columns"
      :key="column.prop || column.label"
      :prop="column.prop"
      :label="column.label"
      :width="column.width"
      :min-width="column.minWidth"
      :fixed="column.fixed"
    >
      <template v-if="column.slot" #default="scope">
        <slot :name="column.slot" v-bind="scope" />
      </template>
    </el-table-column>
    <el-table-column
      v-if="$slots.actions"
      label="操作"
      :width="actionWidth"
      fixed="right"
    >
      <template #default="scope">
        <slot name="actions" v-bind="scope" />
      </template>
    </el-table-column>
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
  },
  actionWidth: {
    type: [Number, String],
    default: 240
  }
})
</script>
