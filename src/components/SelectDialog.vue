<template>
  <el-dialog
    class="select-char-dialog"
    v-model="dialogVisible"
    title="选择角色"
    center
    @opened="onOpened"
    @close="onClose"
  >
    <div>
      <el-select
        v-model="factionFilterModel"
        clearable
        :placeholder="translate('筛选类别')"
        size="small"
      >
        <el-option :label="translate('全部类别')" value=""></el-option>
        <el-option
          v-for="faction in factions"
          :key="faction"
          :label="faction"
          :value="faction"
        ></el-option>
      </el-select>
      <el-checkbox v-model="showNotAddedModel" label="未添加" />
      <el-checkbox v-model="showAddedModel" label="已添加" />
    </div>
    <div class="select-char-container">
      <div
        v-for="char in filteredChars"
        :key="char.id"
        class="select-char-item"
        :class="{ selected: char.selected }"
        @click="onSelect(char)"
      >
        <el-image :src="getAsset(`${char.faction}/${char.name}.webp`)" />
        <div>{{ char.name }}</div>
      </div>
    </div>
    <template #footer>
      <div id="confirm-select" class="dialog-footer">
        <el-button type="primary" @click="dialogVisible = false">
          选好了
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from "vue";

const props = defineProps({
  visible: Boolean,
  filteredChars: Array,
  factions: Array,
  filterConfig: Object,
  translate: Function,
  getAsset: Function,
});

const emit = defineEmits(["update:visible", "update:filter-config", "select-char", "opened", "close"]);

const dialogVisible = ref(props.visible);

// Computed properties for individual filter fields
const factionFilterModel = computed({
  get: () => props.filterConfig?.factionFilter || "",
  set: (value) => {
    emit("update:filter-config", { ...props.filterConfig, factionFilter: value });
  },
});

const showNotAddedModel = computed({
  get: () => props.filterConfig?.showNotAdded ?? true,
  set: (value) => {
    emit("update:filter-config", { ...props.filterConfig, showNotAdded: value });
  },
});

const showAddedModel = computed({
  get: () => props.filterConfig?.showAdded ?? false,
  set: (value) => {
    emit("update:filter-config", { ...props.filterConfig, showAdded: value });
  },
});

watch(
  () => props.visible,
  (newVal) => {
    dialogVisible.value = newVal;
  },
);

watch(dialogVisible, (newVal) => {
  emit("update:visible", newVal);
});

let confirmSelect = null;

const onOpened = () => {
  confirmSelect = document.querySelector("#confirm-select");
  if (confirmSelect) {
    scrollSelectChar();
    document
      .querySelector(".select-char-dialog")
      .parentElement.addEventListener("scroll", scrollSelectChar);
  }
  emit("opened");
};

const onClose = () => {
  if (confirmSelect) {
    document
      .querySelector(".select-char-dialog")
      .parentElement.removeEventListener("scroll", scrollSelectChar);
  }
  confirmSelect = null;
  emit("close");
};

const onSelect = (char) => {
  emit("select-char", char);
};

const scrollSelectChar = () => {
  if (!confirmSelect) {
    return;
  }
  const isOutOfView =
    confirmSelect.getBoundingClientRect().bottom > window.innerHeight;
  const button = confirmSelect.querySelector("button");
  const hasClass = button.classList.contains("floating");
  if (isOutOfView && !hasClass) {
    button.style.width = button.offsetWidth + "px";
    button.classList.add("floating");
  } else if (!isOutOfView && hasClass) {
    button.classList.remove("floating");
    button.style.width = "unset";
  }
};
</script>
