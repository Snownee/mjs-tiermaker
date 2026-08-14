<template>
  <el-dialog class="select-char-dialog" v-model="dialogVisible" :title="translate('选择角色')" center @opened="onOpened"
    @close="onClose">
    <div>
      <div>
        <el-checkbox :model-value="filterConfig.showNotAdded"
          @update:model-value="(value) => updateFilter({ showNotAdded: value })" label="未添加" />
        <el-checkbox :model-value="filterConfig.showAdded"
          @update:model-value="(value) => updateFilter({ showAdded: value })" label="已添加" />
      </div>
      <el-select :model-value="filterConfig.factionFilter"
        @update:model-value="(value) => updateFilter({ factionFilter: value })"
        v-if="filterConfig.showFactionFilter" clearable multiple collapse-tags collapse-tags-tooltip
        :placeholder="translate('类别')" size="small">
        <el-option v-for="faction in factions" :key="faction" :label="faction" :value="faction"></el-option>
      </el-select>
      <el-select v-for="filter in filterConfig.extraFilters" :key="filter.name" class="extra-filter"
        :model-value="filter.value" @update:model-value="(value) => (filter.value = value)" :multiple="filter.multiple"
        clearable collapse-tags collapse-tags-tooltip :placeholder="filter.label" size="small">
        <el-option v-for="option in filter.options" :key="option" :label="option" :value="option"></el-option>
      </el-select>
    </div>
    <div class="select-char-container">
      <div v-for="char in filteredChars" :key="char.id" class="select-char-item" :class="{ selected: char.selected }"
        @click="onSelect(char)">
        <el-image :src="char.imageUrl || getAsset(`${char.faction}/${char.name}.webp`)" />
        <div>{{ char.displayName || char.name }}</div>
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
import { computed, ref, watch } from "vue";

const props = defineProps({
  visible: Boolean,
  filteredChars: Array,
  factions: Array,
  filterConfig: Object,
  translate: Function,
  getAsset: Function,
});

const emit = defineEmits(["update:visible", "select-char", "opened", "close", "update-filter-config"]);

const filterConfig = computed(() => props.filterConfig);

const updateFilter = (patch) => {
  emit("update-filter-config", patch);
};

const dialogVisible = ref(props.visible);

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
