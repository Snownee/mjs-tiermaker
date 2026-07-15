<template>
  <el-button type="primary" @click="openPicker">
    <slot />
  </el-button>
  <input
    ref="fileInput"
    style="display: none;"
    type="file"
    multiple
    accept="image/*"
    @change="handleFileChange"
  />
</template>

<script setup>
import { ref } from "vue";

const emit = defineEmits(["upload"]);

const fileInput = ref(null);

const openPicker = () => {
  fileInput.value?.click();
};

const handleFileChange = (event) => {
  const files = Array.from(event.target.files || []);

  if (files.length > 0) {
    emit("upload", files);
  }

  event.target.value = "";
};
</script>