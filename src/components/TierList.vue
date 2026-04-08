<template>
  <div class="tier-list" :class="{ 'no-drag': noDrag }">
    <div
      v-for="row in tiers"
      :key="row.id"
      class="tier-row"
      :class="{ deleting: row.deleting }"
    >
      <div
        class="tier-label"
        :style="{
          backgroundColor: row.color,
          color: getContrastColor(row.color),
        }"
        @click="openEditTierDialog(row)"
      >
        {{ row.name }}
      </div>

      <VueDraggable
        v-model="row.items"
        group="items"
        class="tier-items"
        :animation="150"
        filter=".hint,.no-drag *"
        @start="onDragStart"
        @end="onDragEnd"
        @click="openSelectDialog(row)"
      >
        <div
          class="item-card"
          v-for="char in row.items"
          :key="char.id"
          @contextmenu.prevent="(e) => openItemMenu(e, char)"
        >
          <el-image :src="getAsset(`${char.faction}/${char.name}.webp`)" />
          <AutoShrinkText :text="char.displayName || char.name" class="name" />
        </div>
        <div
          class="hint-container"
          :class="{ hide: row.items.length > 0 || dragged }"
        >
          <div class="hint">点击添加角色</div>
        </div>
      </VueDraggable>
    </div>
  </div>
</template>

<script setup>
import { VueDraggable } from "vue-draggable-plus";
import AutoShrinkText from "./AutoShrinkText.vue";
import { getContrastColor } from "../utils/color.js";
import { ref } from "vue";

defineProps({
  tiers: Array,
  noDrag: Boolean,
  getAsset: Function,
});

const dragged = ref(false);

const emit = defineEmits([
  "open-edit-tier-dialog",
  "open-select-dialog",
  "open-item-menu",
  "drag-start",
  "drag-end",
]);

const openEditTierDialog = (row) => {
  emit("open-edit-tier-dialog", row);
};

const openSelectDialog = (row) => {
  emit("open-select-dialog", row);
};

const openItemMenu = (e, char) => {
  emit("open-item-menu", e, char);
};

const onDragStart = () => {
  dragged.value = true;
  emit("drag-start");
};

const onDragEnd = () => {
  emit("drag-end");
};
</script>
