<template>
  <main class="tier-container" @mousedown="forcePopover = false">
    <contenteditable tag="h1" v-model="title">Tier List Maker</contenteditable>
    <div class="main-layout">
      <div class="tier-list" :class="{ 'no-drag': noDrag }">
        <div v-for="row in tiers" :key="row.id" class="tier-row">
          <div tag="div" class="tier-label" :style="{ backgroundColor: row.color, color: getContrastColor(row.color) }"
            @click="openEditTierDialog(row)">
            {{ row.name }}
          </div>

          <VueDraggable v-model="row.items" group="items" class="tier-items" :animation="150" filter=".hint,.no-drag *"
            @start="dragged = dragging = true" @end="dragging = false" @click="openSelectDialog(row)">
            <div class="item-card" v-for="char in row.items" :key="char.id">
              <el-image :src="`${asset(`${char.faction}/${char.name}.webp`)}`"></el-image>
              <div>{{ char.name }}</div>
            </div>
            <div class="hint-container" :class="{ hide: row.items.length > 0 || dragged }">
              <div class="hint">点击添加角色</div>
            </div>
          </VueDraggable>
        </div>
      </div>
      <el-button type="primary" @click="resetConfirmDialogVisible = true">重置列表</el-button>
      <el-button type="primary" v-if="isMobile" @click="floatButtonVisible = !floatButtonVisible">浮动按钮：{{
        floatButtonVisible ? '开' : '关' }}</el-button>

      <aside class="float-button-area" v-if="isMobile && floatButtonVisible">
        <el-popover placement="left" title="拖拽模式" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button :icon="Pointer" size="large" circle @click="noDrag = !noDrag" :class="{ selected: !noDrag }" />
          </template>
        </el-popover>
        <el-popover placement="left" title="回到顶部/底部" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button :icon="Bottom" size="large" circle @click="" />
          </template>
        </el-popover>
      </aside>

      <el-dialog class="select-char-dialog" v-model="selectDialogVisible" title="选择角色" center>
        <div>
          <el-checkbox v-model="showNotAdded" label="未添加" />
          <el-checkbox v-model="showAdded" label="已添加" />
        </div>
        <div class="select-char-container">
          <div v-for="char in chars.filter(char => char.selected ? showAdded : showNotAdded)" :key="char.id"
            class="select-char-item" :class="{ selected: char.selected }" @click="select(char)">
            <el-image :src="`${asset(`${char.faction}/${char.name}.webp`)}`"></el-image>
            <div>{{ char.name }}</div>
          </div>
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button type="primary" @click="selectDialogVisible = false" :style="{ minWidth: '50%' }">
              选好了
            </el-button>
          </div>
        </template>
      </el-dialog>

      <el-dialog class="edit-tier-dialog" v-model="tierDialogVisible" title="编辑等级" center :show-close="false">
        <div class="edit-tier-container">
          <el-color-picker v-model="currentTier.color" :predefine="predefineColors" size="large" />
          <el-input v-model="currentTier.name" style="flex: 1" size="large" />
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button type="primary" @click="tierDialogVisible = false">
              确认
            </el-button>
            <el-button type="primary" @click="addTier(currentTier, 'up')">
              添加一栏到上方
            </el-button>
            <el-button type="primary" @click="addTier(currentTier, 'down')">
              添加一栏到下方
            </el-button>
            <el-button type="danger" @click="removeTier(currentTier)">
              删除此栏
            </el-button>
          </div>
        </template>
      </el-dialog>

      <el-dialog class="reset-confirm-dialog" v-model="resetConfirmDialogVisible" title="确认重置" center>
        <div>确定要重置列表吗？此操作不可撤销。</div>
        <template #footer>
          <div class="dialog-footer">
            <el-button @click="resetConfirmDialogVisible = false">
              取消
            </el-button>
            <el-button type="danger" @click="resetList">
              确认重置
            </el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </main>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import contenteditable from 'vue-contenteditable'
import { data } from './data'
import { ElMessage } from 'element-plus'
import { Pointer, Top, Bottom } from '@element-plus/icons-vue'

const chars = ref(processData(data))

function processData(data) {
  data.values.sort((a, b) => a.name.localeCompare(b.name));
  data.values.forEach(value => {
    const [faction, name] = value.name.split('/');
    value.faction = faction;
    value.name = name;
    value.selected = false;
  });
  return data.values
}

const title = ref('Tier List')
const selectDialogVisible = ref(false)
const currentTier = ref(null)
const showNotAdded = ref(true)
const showAdded = ref(false)
const dragging = ref(false)
const dragged = ref(false)
const tierDialogVisible = ref(false)
const resetConfirmDialogVisible = ref(false)
const floatButtonVisible = ref(true)
const noDrag = ref(false)
const isMobile = ref(false);
const mediaQuery = window.matchMedia('(max-width: 767px)');
const forcePopover = ref(true)

const handleDeviceChange = (e) => {
  isMobile.value = e.matches;
};

onMounted(() => {
  noDrag.value = isMobile.value = mediaQuery.matches;
  mediaQuery.addEventListener('change', handleDeviceChange);
  setTimeout(() => {
    forcePopover.value = false;
  }, 1500);
});

onUnmounted(() => {
  mediaQuery.removeEventListener('change', handleDeviceChange);
});

// 初始化等级数据
const predefineColors = ref([
  '#ff7f7f',
  '#ffbf7f',
  '#ffdf7f',
  '#ffff7f',
  '#bfff7f',
  '#7fff7f',
  '#7fffff',
  '#7fbfff',
  '#7f7fff'
])
const initTiers = [
  { id: 1, name: 'S', color: predefineColors.value[0], items: [] },
  { id: 2, name: 'A', color: predefineColors.value[1], items: [] },
  { id: 3, name: 'B', color: predefineColors.value[2], items: [] },
  { id: 4, name: 'C', color: predefineColors.value[3], items: [] },
  { id: 5, name: 'D', color: predefineColors.value[4], items: [] },
]
const tiers = ref(JSON.parse(JSON.stringify(initTiers)))

const resetList = () => {
  Object.assign(tiers.value, JSON.parse(JSON.stringify(initTiers)))
  chars.value.forEach(char => char.selected = false)
  currentTier.value = null
  resetConfirmDialogVisible.value = false
}

const images = import.meta.glob('./assets/**/*.webp', { eager: true, import: 'default' });

const asset = (file) => {
  const path = `./assets/${file}`;

  const url = images[path];

  if (!url) {
    console.warn(`未找到资源文件: ${path}`);
    return '';
  }

  return url;
};

const select = (char) => {
  char.selected = !char.selected
  removeFromList(char)
  if (char.selected) {
    addToList(char, currentTier.value)
  }
}

const removeFromList = (char) => {
  tiers.value.forEach(tier => {
    tier.items = tier.items.filter(item => item.id !== char.id)
  })
}

const addToList = (char, tier) => {
  tier.items.push(char)
}

const openSelectDialog = (tier) => {
  currentTier.value = tier
  selectDialogVisible.value = true
}

const openEditTierDialog = (tier) => {
  currentTier.value = tier
  tierDialogVisible.value = true
}

const addTier = (tier, position) => {
  const index = tiers.value.findIndex(t => t.id === tier.id)
  const color = predefineColors.value[(predefineColors.value.indexOf(tier.color) + 1) % predefineColors.value.length]
  const newTier = {
    id: Date.now(),
    name: 'New',
    color: color,
    items: []
  }
  if (position === 'up') {
    tiers.value.splice(index, 0, newTier)
  } else {
    tiers.value.splice(index + 1, 0, newTier)
  }
  tierDialogVisible.value = false
}

const removeTier = (tier) => {
  if (tiers.value.length === 1) {
    ElMessage.error('至少保留一个等级')
    return
  }
  const index = tiers.value.findIndex(t => t.id === tier.id)
  tiers.value.splice(index, 1)
  tierDialogVisible.value = false
}

const getContrastColor = (hexColor) => {
  // 1. 去掉 # 号并转换为 RGB
  const hex = hexColor.replace('#', '');
  const r = parseInt(hex.substr(0, 2), 16);
  const g = parseInt(hex.substr(2, 2), 16);
  const b = parseInt(hex.substr(4, 2), 16);

  // 2. 计算亮度 (根据人眼感官加权)
  // 公式中的除以 255 是为了归一化
  const brightness = (r * 212.6 + g * 715.2 + b * 72.2) / 1000;

  // 3. 返回黑色或白色 (128 是 256 的中间值)
  return brightness > 128 ? '#000000' : '#FFFFFF';
}
</script>