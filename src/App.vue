<template>
  <main class="tier-container" @mousedown="forcePopover = false">
    <contenteditable tag="h1" v-model="title" style="min-width: 20px">
    </contenteditable>
    <contenteditable tag="span" v-model="subtitle" style="min-width: 20px">
    </contenteditable>
    <div class="main-layout">
      <TierList v-model:name-visible="cardNameVisible" :tiers="tiers" :no-drag="noDrag" :translate="translate"
        :get-asset="asset" @open-edit-tier-dialog="openEditTierDialog" @open-select-dialog="openSelectDialog"
        @open-item-menu="openItemMenu" @drag-start="dragging = true" @drag-end="dragging = false" />
      <el-tooltip :visible="itemMenuChar !== null" :virtual-ref="itemMenuTarget" placement="top" persistent
        virtual-triggering :popper-options="{
          modifiers: [
            {
              name: 'computeStyles',
              options: {
                adaptive: false,
                enabled: false,
              },
            },
          ],
        }">
        <template #content>
          <div class="item-card-menu" v-click-outside="itemMenuOutside">
            <span @click="itemMenuDelete">删除</span>
          </div>
        </template>
      </el-tooltip>
      <div class="buttons">
        <el-dropdown :show-arrow="false" v-if="!isVanilla">
          <el-button type="primary" class="preset-button">
            <div>{{ preset || "📦使用预设" }}</div>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="item in presets" :key="item.name" @click="usePreset(item)">{{ item.name
              }}</el-dropdown-item>
              <el-dropdown-item v-if="presets.length === 0" disabled>暂无预设</el-dropdown-item>
              <el-dropdown-item v-if="uiSettings.submitPresetUrl" @click="submitPreset" divided>预设投稿</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="share" v-if="!isVanilla">👋分享列表</el-button>
        <el-button type="primary" @click="clickResetConfirm">🧹重置列表</el-button>
        <el-button type="primary" v-if="isMobile" @click="floatButtonVisible = !floatButtonVisible">👁️浮动按钮：{{
          floatButtonVisible ? "开" : "关" }}</el-button>
        <ImageUploader @upload="addLocalImages">📤{{ translate('本地图片') }}</ImageUploader>
        <el-button type="primary" v-if="isVanilla" @click="cardNameVisible = !cardNameVisible">🔠显示文字：{{
          cardNameVisible ? "开" : "关" }}</el-button>
        <el-dropdown :show-arrow="false" v-if="isVanilla">
          <el-button type="primary">
            <div>📏卡片尺寸</div>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="scale in [50, 75, 100, 125, 150, 175, 200]" :key="scale"
                @click="vanillaCardScale = scale">
                {{ scale }}%{{ vanillaCardScale === scale ? " ✅" : "" }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
      <div>
        <el-text>
          <a :href="authorUrl" target="_blank">作者：Snownee</a>
          - 最后更新：{{ buildTime }}
        </el-text>
      </div>

      <aside class="float-button-area" v-if="isMobile && floatButtonVisible">
        <el-popover placement="left" title="拖拽模式" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button size="large" circle @click="noDrag = !noDrag" :class="{ selected: !noDrag }">
              👆
            </el-button>
          </template>
        </el-popover>
        <!-- <el-popover placement="left" title="回到顶部/底部" trigger="hover" :visible="forcePopover">
          <template #reference>
            <el-button :icon="Bottom" size="large" circle @click="" />
          </template>
        </el-popover> -->
      </aside>

      <SelectDialog v-model:visible="selectDialogVisible" :filtered-chars="filteredChars" :factions="factions"
        :filter-config="filterConfig" :translate="translate" :get-asset="asset" @select-char="select" />

      <EditTierDialog v-model:visible="tierDialogVisible" :current-tier="currentTier"
        :predefine-colors="PREDEFINE_COLORS" @add-tier="handleAddTier" @remove-tier="handleRemoveTier" />

      <FallbackCopyDialog v-model:visible="fallbackCopyDialogVisible" :copy-text="fallbackCopy" />
    </div>
  </main>
</template>

<script setup>
import { namespace, data, presets, lang, uiSettings } from "./data";
import { ref, onMounted, onUnmounted, watch } from "vue";
import contenteditable from "vue-contenteditable";
import {
  ElMessage,
  ElMessageBox,
  ClickOutside as vClickOutside,
} from "element-plus";
import { ArrowDown } from "@element-plus/icons-vue";
import ImageUploader from "./components/ImageUploader.vue";
import TierList from "./components/TierList.vue";
import SelectDialog from "./components/SelectDialog.vue";
import EditTierDialog from "./components/EditTierDialog.vue";
import FallbackCopyDialog from "./components/FallbackCopyDialog.vue";
import { useTiers } from "./composables/useTiers.js";
import { useCharacters } from "./composables/useCharacters.js";
import { usePersistence } from "./composables/usePersistence.js";
import { usePlatform } from "./composables/usePlatform.js";
import { PREDEFINE_COLORS } from "./utils/constants.js";

const buildTime = __BUILD_TIME__;

const translate = (key) => {
  const translated = lang[key];
  return translated !== undefined ? translated : key;
};

const msg = (type, message) => {
  const options = { type, message };
  // options.appendTo = '.tier-container'
  // options.duration = 0
  ElMessage(options);
};

const title = ref(translate("title"));
const subtitle = ref(translate("subtitle"));
const localChars = ref([]);
const nextLocalCharId = ref(-1);

const isVanilla = namespace === "v";
const cardNameVisible = ref(true);
const vanillaCardScale = ref(100);
const vanillaCardWidth = ref(0);
const vanillaCardHeight = ref(0);
watch(vanillaCardScale, _ => updateVanillaCardSize());
watch(cardNameVisible, _ => updateVanillaCardSize());

// Initialize composables
const {
  chars,
  factions,
  filteredChars,
  filterConfig,
  filterChars,
  select: selectChar,
} = useCharacters(data, uiSettings, localChars);
const {
  tiers,
  resetList,
  addTier: addTierToList,
  removeTier: removeTierFromList,
  addToList,
  removeFromList,
  updatePresetTimestamp,
  shouldUpdatePreset,
} = useTiers(chars, msg);
const { saveList, loadList, saveToLocalStorage } = usePersistence(
  tiers,
  chars,
  title,
  subtitle,
  namespace,
  msg,
);

const selectDialogVisible = ref(false);
const currentTier = ref(null);
const dragging = ref(false);
const tierDialogVisible = ref(false);
const floatButtonVisible = ref(true);
const noDrag = ref(false);
const isMobile = ref(false);
const mediaQuery = window.matchMedia("(max-width: 767px)");
const forcePopover = ref(true);
const preset = ref();
const fallbackCopyDialogVisible = ref(false);
const fallbackCopy = ref("");

const VANILLA_CARD_DEFAULTS = {
  "--list-item-padding": "1px",
  "--list-item-image-width": "84px",
  "--list-item-image-height": "112px",
  "--list-item-image-width-mobile": "70px",
  "--list-item-image-height-mobile": "93px",
  "--list-item-width": "84px",
  "--list-item-height": "128px",
  "--select-item-width": "84px",
  "--select-item-image-width": "84px",
  "--select-item-image-height": "112px",
  "--select-item-width-mobile": "70px",
  "--select-item-image-height-mobile": "93px",
};

const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

const applyCardCssVars = (vars) => {
  Object.entries(vars).forEach(([key, value]) => {
    document.documentElement.style.setProperty(key, value);
  });
};

const readImageSize = (file) =>
  new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const image = new Image();

    image.onload = () => {
      resolve({
        width: image.naturalWidth,
        height: image.naturalHeight,
      });
      URL.revokeObjectURL(objectUrl);
    };

    image.onerror = (error) => {
      URL.revokeObjectURL(objectUrl);
      reject(error);
    };

    image.src = objectUrl;
  });

const updateVanillaCardSize = () => {
  if (!isVanilla) {
    return;
  }
  try {
    const width = vanillaCardWidth.value;
    const height = vanillaCardHeight.value;
    if (!width || !height) {
      return;
    }
    const aspectRatio = width / height;
    const baseArea = 84 * 112;

    let imageWidth = Math.sqrt(baseArea * aspectRatio);
    let imageHeight = imageWidth / aspectRatio;

    imageWidth = clamp(Math.round(imageWidth), 64, 140);
    imageHeight = clamp(Math.round(imageHeight), 80, 170);

    let mobileWidth = clamp(Math.round(imageWidth * 0.84), 56, 112);
    let mobileHeight = clamp(Math.round(imageHeight * 0.84), 72, 136);

    const scaleFactor = vanillaCardScale.value / 100;
    imageWidth = Math.round(imageWidth * scaleFactor);
    imageHeight = Math.round(imageHeight * scaleFactor);
    mobileWidth = Math.round(mobileWidth * scaleFactor);
    mobileHeight = Math.round(mobileHeight * scaleFactor);

    applyCardCssVars({
      "--list-item-padding": "1px",
      "--list-item-image-width": `${imageWidth}px`,
      "--list-item-image-height": `${imageHeight}px`,
      "--list-item-image-width-mobile": `${mobileWidth}px`,
      "--list-item-image-height-mobile": `${mobileHeight}px`,
      "--list-item-width": `${imageWidth}px`,
      "--list-item-height": `${imageHeight + (cardNameVisible.value ? 16 : 0)}px`,
      "--select-item-width": `${imageWidth}px`,
      "--select-item-image-width": `${imageWidth}px`,
      "--select-item-image-height": `${imageHeight}px`,
      "--select-item-width-mobile": `${mobileWidth}px`,
      "--select-item-image-height-mobile": `${mobileHeight}px`,
    });
  } catch (error) {
    console.warn("读取图片尺寸失败，使用默认卡片尺寸", error);
    applyCardCssVars(VANILLA_CARD_DEFAULTS);
  }
};

const handleDeviceChange = (e) => {
  isMobile.value = e.matches;
  if (!isMobile.value) {
    noDrag.value = false;
  }
};

const { platform, authorUrl } = usePlatform(window.location.hostname);

onMounted(() => {
  if (isVanilla) {
    applyCardCssVars(VANILLA_CARD_DEFAULTS);
    const settings = JSON.parse(localStorage.getItem(`${namespace}_tier_list_settings`) || "{}");
    vanillaCardScale.value = settings.cardScale || vanillaCardScale.value;
    cardNameVisible.value = settings.cardNameVisible ?? cardNameVisible.value;
  }

  document.title = translate("doc_title");
  noDrag.value = isMobile.value = mediaQuery.matches;
  mediaQuery.addEventListener("change", handleDeviceChange);
  window.addEventListener("scroll", itemMenuOutside);
  if (platform === "taptap") {
    document.body.classList.add("taptap");
  }
  setTimeout(() => {
    forcePopover.value = false;
    document.body.classList.add("mounted");
  }, 1500);
  if (isVanilla) {
    return;
  }
  // 尝试从 URL 参数加载数据
  const params = new URLSearchParams(window.location.search);
  // 尝试加载预设
  if (params.has("p")) {
    const preset = presets.find((p) => p.name === params.get("p"));
    if (preset) {
      usePreset(preset);
      return;
    }
  }
  if (window.location.search.length > 1 && params.keys().some(() => true)) {
    if (loadList(window.location.search.slice(1))) {
      window.history.replaceState(
        {},
        document.title,
        window.location.origin + window.location.pathname,
      );
      return;
    }
  }
  const saveData = localStorage.getItem(`${namespace}_tier_list_tiers`);
  if (saveData && loadList(saveData)) {
    return;
  }
  if (presets.length > 0) {
    usePreset(presets[0]);
  }
});

onUnmounted(() => {
  mediaQuery.removeEventListener("change", handleDeviceChange);
  localChars.value.forEach((char) => {
    if (char.imageUrl?.startsWith("blob:")) {
      URL.revokeObjectURL(char.imageUrl);
    }
  });
});

watch(
  [title, subtitle, tiers],
  () => {
    if (shouldUpdatePreset()) {
      preset.value = undefined;
    }
    if (!dragging.value && !isVanilla) {
      saveToLocalStorage(true);
    }
  },
  { deep: true },
);

if (isVanilla) {
  watch(
    [vanillaCardScale, cardNameVisible],
    () => {
      localStorage.setItem(
        `${namespace}_tier_list_settings`,
        JSON.stringify({
          cardScale: vanillaCardScale.value,
          cardNameVisible: cardNameVisible.value,
        })
      );
    },
    { deep: true },
  );
}

const images = import.meta.glob("./assets/**/*.webp", {
  eager: true,
  import: "default",
});

const asset = (file) => {
  const path = `./assets/${file}`;

  const url = images[path];

  if (!url) {
    console.warn(`未找到资源文件: ${path}`);
    return "";
  }

  return url;
};

const select = (char) => {
  selectChar(char, currentTier.value, addToList, removeFromList);
};

const openSelectDialog = (tier) => {
  if (isVanilla && localChars.value.length === 0) {
    msg("warning", "请先点击页面下方的按钮添加一些图片");
    return;
  }
  filterChars();
  currentTier.value = tier;
  selectDialogVisible.value = true;
};

const itemMenuVPosition = ref({ top: 0, left: 0, width: 0, height: 0 });
const itemMenuTarget = ref({
  getBoundingClientRect: () => itemMenuVPosition.value,
});
const itemMenuChar = ref(null);

const itemMenuOutside = (e) => {
  if (itemMenuChar.value) {
    e.preventDefault();
    e.stopPropagation();
    itemMenuChar.value = null;
  }
};

const itemMenuDelete = () => {
  const char = itemMenuChar.value;
  if (char) {
    itemMenuChar.value = null;
    removeFromList(char);
  }
};

const openItemMenu = (e, char) => {
  // msg('info', `角色：${char.name}\n类别：${char.faction}`)
  const { top, left, width, height } = e.currentTarget.getBoundingClientRect();
  itemMenuVPosition.value = { top, left, width, height };
  itemMenuChar.value = char;
};

const openEditTierDialog = (tier) => {
  currentTier.value = tier;
  tierDialogVisible.value = true;
};

const handleAddTier = (position) => {
  addTierToList(currentTier.value, position);
  tierDialogVisible.value = false;
};

const handleRemoveTier = () => {
  removeTierFromList(currentTier.value);
  tierDialogVisible.value = false;
};

const share = () => {
  const base = window.location.origin + window.location.pathname;
  if (preset.value) {
    copyUrl(`${document.title} - ${preset.value} - ${base}?p=${preset.value}`);
    return;
  }
  const result = saveList();
  if (result === null) {
    copyUrl(`${document.title} - ${base}`);
    return;
  }
  console.log(result);
  copyUrl(`${document.title} - ${title.value || "未命名"} - ${base}?${result}`);
};

const copyUrl = async (url) => {
  try {
    await navigator.clipboard.writeText(url);
    msg("success", "链接已复制到剪贴板");
  } catch (err) {
    msg("error", "复制失败: " + err);
    console.error("复制失败: ", err);
    fallbackCopy.value = url;
    fallbackCopyDialogVisible.value = true;
  }
};

const usePreset = (newPreset) => {
  loadList(newPreset.save);
  if (preset.value !== newPreset.name) {
    updatePresetTimestamp();
    preset.value = newPreset.name;
  }
};

const submitPreset = () => {
  ElMessageBox.confirm(
    "感谢使用本应用，如有建议或是想要投稿预设，可以向我留言👇👇👇",
    "预设投稿",
    {
      confirmButtonText: "去帖子留言",
      type: "info",
      center: true,
      showCancelButton: false,
    },
  )
    .then(() => {
      window.open(uiSettings.submitPresetUrl, "_blank");
    })
    .catch(() => { });
};

const clickResetConfirm = () => {
  ElMessageBox.confirm("确定要重置列表吗？此操作不可撤销。", "你即将清空列表", {
    confirmButtonText: "确认重置",
    confirmButtonType: "danger",
    type: "warning",
    center: true,
  })
    .then(() => {
      resetList();
      msg("success", "列表已重置");
    })
    .catch(() => { });
};

const addLocalImages = async (files) => {
  const imageFiles = files.filter((file) => file.type.startsWith("image/"));

  if (isVanilla && localChars.value.length === 0 && imageFiles.length > 0) {
    const { width, height } = await readImageSize(imageFiles[0]);
    vanillaCardWidth.value = width;
    vanillaCardHeight.value = height;
    updateVanillaCardSize();
  }

  const newChars = imageFiles
    .map((file) => {
      const name = file.name.replace(/\.[^.]+$/, "") || file.name;

      return {
        id: nextLocalCharId.value--,
        name,
        displayName: name,
        faction: "本地",
        selected: false,
        imageUrl: URL.createObjectURL(file),
      };
    });

  if (newChars.length === 0) {
    msg("warning", "请选择图片文件");
    return;
  }

  localChars.value = [...localChars.value, ...newChars];
  msg(
    "success",
    `已添加 ${newChars.length} 个${translate('角色')}。${translate('请注意，本地角色会在刷新页面后丢失。')}`,
  );
};
</script>
