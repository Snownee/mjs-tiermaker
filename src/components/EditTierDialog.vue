<template>
  <el-dialog class="edit-tier-dialog" v-model="dialogVisible" title="编辑等级" center :show-close="false">
    <div class="edit-tier-container">
      <el-color-picker :model-value="currentTier.color" @update:model-value="(value) => updateTier({ color: value })"
        :predefine="predefineColors" size="large" />
      <el-input ref="input" :model-value="currentTier.name" @update:model-value="(value) => updateTier({ name: value })"
        style="flex: 1" size="large" />
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="dialogVisible = false">
          确认
        </el-button>
        <el-button type="primary" @click="addTier('up')">
          添加一栏到上方
        </el-button>
        <el-button type="primary" @click="addTier('down')">
          添加一栏到下方
        </el-button>
        <el-button type="danger" @click="removeTier"> 删除此栏 </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from "vue";
import { PREDEFINE_COLORS } from "../utils/constants.js";

const props = defineProps({
  visible: Boolean,
  currentTier: Object,
  predefineColors: {
    type: Array,
    default: () => PREDEFINE_COLORS,
  },
});

const emit = defineEmits(["update:visible", "add-tier", "remove-tier", "update-tier"]);

const dialogVisible = ref(false);
const input = ref(null);

watch(
  () => props.visible,
  (newVal) => {
    dialogVisible.value = newVal;
  },
);

watch(dialogVisible, (newVal) => {
  if (newVal) {
    // 打开对话框时自动聚焦输入框
    setTimeout(() => {
      if (input.value) {
        input.value.focus();
      }
    }, 100);
  }
  emit("update:visible", newVal);
});

const addTier = (position) => {
  emit("add-tier", position);
};

const updateTier = (patch) => {
  emit("update-tier", patch);
};

const removeTier = () => {
  emit("remove-tier");
};
</script>
