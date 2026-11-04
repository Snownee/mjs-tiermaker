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
    <div class="select-char-container" :class="{ 'drag-select': isDragging }" @touchmove="onContainerTouchMove"
      @touchend="onContainerTouchEnd" @touchcancel="onContainerTouchEnd">
      <div v-for="char in filteredChars" :key="char.id" class="select-char-item" :class="{ selected: char.selected }"
        :data-char-id="char.id" @mousedown.left.prevent="onCharMouseDown(char)"
        @mouseenter="onCharMouseEnter(char)" @click="onCharClick(char)"
        @touchstart="onCharTouchStart(char, $event)" @contextmenu.prevent>
        <el-image :src="char.imageUrl || getAsset(`${char.faction}/${char.name}.webp`)" />
        <div>{{ char.displayName || char.name }}</div>
      </div>
    </div>
    <template #footer>
      <div id="confirm-select" class="dialog-footer">
        <div class="drag-select-hint">
          {{
            isTouchInput
              ? "长按角色后拖动，可批量加入；从已加入的角色开始拖动，则批量移出"
              : "按住鼠标左键划过角色，可批量加入；从已加入的角色开始拖动，则批量移出"
          }}
        </div>
        <el-button type="primary" @click="dialogVisible = false">
          选好了
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { vibrate } from "../utils/haptics.js";

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

// 根据最近一次使用的指针类型显示对应提示；尚未操作时按主指针类型判断
const isTouchInput = ref(window.matchMedia("(pointer: coarse)").matches);

const onPointerDown = (event) => {
  isTouchInput.value = event.pointerType !== "mouse";
};

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
  stopDrag();
  endTouch();
  emit("close");
};

// 拖动选择：dragMode 为 true 表示正在批量加入，false 表示正在批量移出
let dragMode = null;
// 按下鼠标时已由 mousedown 处理过选中状态，阻止随后的 click 再切换一次
let clickGuard = false;
const isDragging = ref(false);

// 触屏：长按进入拖动选择，未长按的滑动仍用于滚动列表
const TOUCH_LONG_PRESS_MS = 350;
const TOUCH_MOVE_TOLERANCE = 10;
// 触屏拖动结束后浏览器可能补发一次鼠标事件，这段时间内忽略合成事件；
// 下一次触摸开始时会立即解除，避免影响随后的点按
const SYNTHETIC_MOUSE_IGNORE_MS = 400;

let touchTimer = null;
let touchStartPoint = null;
let touchDragging = false;
let suppressSyntheticMouse = false;

const applyDrag = (char) => {
  if (char.selected === dragMode) {
    return;
  }
  emit("select-char", char);
};

const onCharMouseDown = (char) => {
  if (suppressSyntheticMouse) {
    return;
  }
  clickGuard = true;
  dragMode = !char.selected;
  isDragging.value = true;
  applyDrag(char);
};

const onCharMouseEnter = (char) => {
  if (dragMode === null) {
    return;
  }
  applyDrag(char);
};

const onCharClick = (char) => {
  if (suppressSyntheticMouse) {
    return;
  }
  if (clickGuard) {
    clickGuard = false;
    return;
  }
  emit("select-char", char);
};

const onCharTouchStart = (char, event) => {
  if (event.touches.length !== 1) {
    return;
  }
  // 新的触摸开始，解除上一次拖动结束后的合成鼠标事件屏蔽
  suppressSyntheticMouse = false;
  const touch = event.touches[0];
  touchStartPoint = { x: touch.clientX, y: touch.clientY };
  touchDragging = false;
  touchTimer = setTimeout(() => {
    touchTimer = null;
    touchDragging = true;
    dragMode = !char.selected;
    isDragging.value = true;
    applyDrag(char);
    vibrate(10);
  }, TOUCH_LONG_PRESS_MS);
};

const onContainerTouchMove = (event) => {
  if (!touchStartPoint) {
    return;
  }
  const touch = event.touches[0];
  if (!touchDragging) {
    // 未长按时移动视为滚动，取消长按
    const moved =
      Math.hypot(
        touch.clientX - touchStartPoint.x,
        touch.clientY - touchStartPoint.y,
      ) > TOUCH_MOVE_TOLERANCE;
    if (moved) {
      clearTimeout(touchTimer);
      touchTimer = null;
      touchStartPoint = null;
    }
    return;
  }
  event.preventDefault();
  const item = document
    .elementFromPoint(touch.clientX, touch.clientY)
    ?.closest(".select-char-item");
  const char = props.filteredChars.find(
    (c) => String(c.id) === item?.dataset.charId,
  );
  if (char) {
    applyDrag(char);
  }
};

const onContainerTouchEnd = (event) => {
  endTouch(event);
};

const endTouch = (event) => {
  if (touchTimer) {
    clearTimeout(touchTimer);
    touchTimer = null;
  }
  if (touchDragging) {
    // 阻止拖动结束后浏览器补发 mousedown/click
    if (event?.cancelable) {
      event.preventDefault();
    }
    suppressSyntheticMouse = true;
    setTimeout(() => {
      suppressSyntheticMouse = false;
    }, SYNTHETIC_MOUSE_IGNORE_MS);
    dragMode = null;
    isDragging.value = false;
  }
  touchDragging = false;
  touchStartPoint = null;
};

const stopDrag = () => {
  dragMode = null;
  isDragging.value = false;
  if (clickGuard) {
    // 拖动结束时 click 可能不会触发，等 click 派发完再清理
    setTimeout(() => {
      clickGuard = false;
    }, 0);
  }
};

onMounted(() => {
  window.addEventListener("mouseup", stopDrag);
  window.addEventListener("blur", stopDrag);
  window.addEventListener("pointerdown", onPointerDown);
});

onUnmounted(() => {
  window.removeEventListener("mouseup", stopDrag);
  window.removeEventListener("blur", stopDrag);
  window.removeEventListener("pointerdown", onPointerDown);
  endTouch();
});

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
