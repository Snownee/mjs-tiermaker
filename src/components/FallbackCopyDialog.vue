<template>
  <el-dialog
    class="fallback-copy-dialog"
    v-model="dialogVisible"
    title="请复制"
    center
  >
    <div>
      <el-input
        v-model="localCopyText"
        style="width: 100%"
        :rows="6"
        type="textarea"
        placeholder=""
      />
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button type="primary" @click="dialogVisible = false">
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from "vue";

const props = defineProps({
  visible: Boolean,
  copyText: String,
});

const emit = defineEmits(["update:visible"]);

const dialogVisible = ref(props.visible);
const localCopyText = ref(props.copyText);

watch(
  () => props.visible,
  (newVal) => {
    dialogVisible.value = newVal;
  },
);

watch(
  () => props.copyText,
  (newVal) => {
    localCopyText.value = newVal;
  },
);

watch(dialogVisible, (newVal) => {
  emit("update:visible", newVal);
});
</script>
