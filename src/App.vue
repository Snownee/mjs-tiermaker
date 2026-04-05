<template>
  <main class="tier-container" @mousedown="forcePopover = false">
    <contenteditable tag="h1" v-model="title" style="min-width: 20px">
    </contenteditable>
    <contenteditable tag="span" v-model="subtitle" style="min-width: 20px;">
    </contenteditable>
    <div class="main-layout">
      <div class="tier-list" :class="{ 'no-drag': noDrag }">
        <div v-for="row in tiers" :key="row.id" class="tier-row" :class="{ deleting: row.deleting }">
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
      <div class="buttons">
        <el-dropdown :show-arrow="false">
          <el-button type="primary" class="preset-button">
            <div>{{ preset || '使用预设' }}</div>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="item in presets" :key="item.name" @click="usePreset(item)">{{ item.name
              }}</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="share">分享列表</el-button>
        <el-button type="primary" @click="resetConfirmDialogVisible = true">重置列表</el-button>
        <el-button type="primary" v-if="isMobile" @click="floatButtonVisible = !floatButtonVisible">浮动按钮：{{
          floatButtonVisible ? '开' : '关' }}</el-button>
      </div>
      <div>
        <el-text>
          <a href="https://www.taptap.cn/user/757224223" target="_blank">作者：Snownee</a>
          -
          最后更新：{{ buildTime }}
        </el-text>
      </div>

      <aside class="float-button-area" v-if="isMobile && floatButtonVisible">
        <el-popover placement="left" title="拖拽模式" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button :icon="Pointer" size="large" circle @click="noDrag = !noDrag" :class="{ selected: !noDrag }" />
          </template>
        </el-popover>
        <!-- <el-popover placement="left" title="回到顶部/底部" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button :icon="Bottom" size="large" circle @click="" />
          </template>
        </el-popover> -->
      </aside>

      <el-dialog class="select-char-dialog" v-model="selectDialogVisible" title="选择角色" center>
        <div>
          <el-select v-model="factionFilter" clearable :placeholder="translate('筛选类别')" size="small">
            <el-option :label="translate('全部类别')" value=""></el-option>
            <el-option v-for="faction in factions" :key="faction" :label="faction" :value="faction"></el-option>
          </el-select>
          <el-checkbox v-model="showNotAdded" label="未添加" />
          <el-checkbox v-model="showAdded" label="已添加" />
        </div>
        <div class="select-char-container">
          <div v-for="char in filteredChars()" :key="char.id" class="select-char-item"
            :class="{ selected: char.selected }" @click="select(char)">
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

      <el-dialog class="fallback-copy-dialog" v-model="fallbackCopyDialogVisible" title="请复制" center>
        <div>
          <el-input v-model="fallbackCopy" style="width: 100%" :rows="6" type="textarea" placeholder="" />
        </div>
        <template #footer>
          <div class="dialog-footer">
            <el-button type="primary" @click="fallbackCopyDialogVisible = false">
              关闭
            </el-button>
          </div>
        </template>
      </el-dialog>
    </div>
  </main>
</template>

<script setup>
import { namespace, data, presets, lang } from './data'
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'
import contenteditable from 'vue-contenteditable'
import { ElMessage } from 'element-plus'
import { Pointer, ArrowDown, Top, Bottom } from '@element-plus/icons-vue'
import { load, save } from './save'

const buildTime = __BUILD_TIME__;

const translate = (key) => {
  return lang[key] || key
}

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

const factions = [...new Set(chars.value.map(char => char.faction))]

const title = ref(translate('title'))
const subtitle = ref(translate('subtitle'))
const selectDialogVisible = ref(false)
const currentTier = ref(null)
const showNotAdded = ref(true)
const showAdded = ref(false)
const factionFilter = ref('')
const dragging = ref(false)
const dragged = ref(false)
const tierDialogVisible = ref(false)
const resetConfirmDialogVisible = ref(false)
const floatButtonVisible = ref(true)
const noDrag = ref(false)
const isMobile = ref(false);
const mediaQuery = window.matchMedia('(max-width: 767px)');
const forcePopover = ref(true)
const preset = ref(undefined)
const fallbackCopyDialogVisible = ref(false)
const fallbackCopy = ref('')

const handleDeviceChange = (e) => {
  isMobile.value = e.matches;
};

const taptap = window.location.hostname.includes('tap')

onMounted(() => {
  noDrag.value = isMobile.value = mediaQuery.matches;
  mediaQuery.addEventListener('change', handleDeviceChange);
  if (taptap) {
    document.body.classList.add('taptap')
  }
  setTimeout(() => {
    forcePopover.value = false;
    document.body.classList.add('mounted')
  }, 1500);
  // 尝试从 URL 参数加载数据
  const params = new URLSearchParams(window.location.search);
  // 尝试加载预设
  if (params.has('p')) {
    const preset = presets.find(p => p.name === params.get('p'))
    if (preset) {
      usePreset(preset)
      return
    }
  }
  if (window.location.search.length > 1 && params.keys().some(_ => true)) {
    if (loadList(window.location.search.slice(1))) {
      window.history.replaceState({}, document.title, window.location.origin + window.location.pathname);
      return
    }
  }
  const saveData = localStorage.getItem('mjs_tier_list_tiers');
  if (saveData && loadList(saveData)) {
    return
  }
  usePreset(presets[0])
});

onUnmounted(() => {
  mediaQuery.removeEventListener('change', handleDeviceChange);
});

// 初始化等级数据
const predefineColors = [
  '#ff7f7f',
  '#ffbf7f',
  '#ffdf7f',
  '#ffff7f',
  '#bfff7f',
  '#7fff7f',
  '#7fffff',
  '#7fbfff',
  '#7f7fff'
]
const initTiers = [
  { id: 1, name: '夯', color: predefineColors[0], items: [] },
  { id: 2, name: '顶级', color: predefineColors[1], items: [] },
  { id: 3, name: '人上人', color: predefineColors[2], items: [] },
  { id: 4, name: 'NPC', color: predefineColors[3], items: [] },
  { id: 5, name: '拉完了', color: predefineColors[4], items: [] },
]
const tiers = ref(JSON.parse(JSON.stringify(initTiers)))
let lastTimeUsePreset = Date.now()

watch([title, subtitle, tiers], _ => {
  if (Date.now() - lastTimeUsePreset > 500) {
    preset.value = undefined
  }
  if (!dragging.value) {
    const result = saveList(true);
    if (result) {
      localStorage.setItem('mjs_tier_list_tiers', result)
    }
  }
}, { deep: true })

const resetList = () => {
  tiers.value = JSON.parse(JSON.stringify(initTiers))
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
  if (tiers.value.length >= 14) {
    msg('error', '已达到栏目数量上限')
    return
  }
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
    msg('error', '至少保留一个等级')
    return
  }
  tierDialogVisible.value = false
  tier.deleting = true

  setTimeout(() => {
    tier.items.forEach(char => char.selected = false)
    const index = tiers.value.findIndex(t => t.id === tier.id)
    tiers.value.splice(index, 1)
  }, 300)
}

const share = () => {
  const base = window.location.origin + window.location.pathname
  if (preset.value) {
    copyUrl(`${document.title} - ${preset.value} - ${base}?p=${preset.value}`)
    return
  }
  const result = saveList()
  if (result === null) {
    copyUrl(`${document.title} - ${base}`)
    return
  }
  console.log(result);
  copyUrl(`${document.title} - ${title.value || '未命名'} - ${base}?${result}`)
}

const saveList = (allowEmpty = false) => {
  if (!allowEmpty && tiers.value.every(tier => tier.items.length === 0)) {
    return null
  }
  const tiersData = []
  tiers.value.forEach(tier => {
    tiersData.push({
      name: tier.name,
      color: tier.color,
      items: tier.items.map(item => item.id)
    })
  })
  return save({
    title: title.value || '',
    subtitle: subtitle.value || '',
    tiers: tiersData
  })
}

const loadList = (saveData) => {
  if (typeof saveData === 'string') {
    try {
      saveData = load(saveData)
    } catch (error) {
      saveData = { error: 3 }
    }
    if (saveData.error) {
      msg('error', '读取数据时出错')
      return false
    }
  }
  chars.value.forEach(char => char.selected = false)
  title.value = saveData.title
  subtitle.value = saveData.subtitle
  // console.log(JSON.stringify(saveData));

  const newTiers = saveData.tiers.map(tier => {
    tier.items = tier.items.map(itemId => {
      const char = chars.value.find(c => c.id === itemId)
      if (char) {
        char.selected = true
        return char
      }
      return null
    }).filter(item => item !== null)
    return tier
  })
  let nextId = 1
  for (const tier of newTiers) {
    tier.id = nextId++
  }

  tiers.value = newTiers
  return true
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

const copyUrl = async (url) => {
  try {
    await navigator.clipboard.writeText(url);
    msg('success', '链接已复制到剪贴板')
  } catch (err) {
    msg('error', '复制失败: ' + err)
    console.error('复制失败: ', err);
    fallbackCopy.value = url
    fallbackCopyDialogVisible.value = true
  }
};

const usePreset = (newPreset) => {
  loadList(newPreset.save)
  if (preset.value !== newPreset.name) {
    lastTimeUsePreset = Date.now()
    preset.value = newPreset.name
  }
}

const filteredChars = () => {
  return chars.value.filter(char => (char.selected ? showAdded.value : showNotAdded.value) && (char.faction === factionFilter.value || factionFilter.value === '' || factionFilter.value === undefined))
}

const msg = (type, message) => {
  const options = { type, message }
  // options.appendTo = '.tier-container'
  // options.duration = 0
  ElMessage(options)
}
</script>