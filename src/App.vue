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
      <div v-if="itemViewChar" class="item-view-mask" :class="{ 'fade-out': itemViewFadeOut }"
        @mousedown="closeItemView('cancel')" @wheel.prevent="onItemViewWheel">
        <div class="item-view">
          <div ref="itemViewStage" class="item-view-stage"
            :class="{ 'no-transition': !itemViewTransition }">
            <div class="item-view-img-wrap" :style="itemViewWrapStyle">
              <el-image class="item-view-img"
                :src="itemViewChar.imageUrl || asset(`${itemViewChar.faction}/${itemViewChar.name}.webp`)"
                fit="contain" />
            </div>
          </div>
          <AutoShrinkText :text="itemViewChar.displayName || itemViewChar.name" class="item-view-name"
            @mousedown.stop />
          <div class="item-view-menu" @mousedown.stop>
            <el-button-group class="item-view-btn-group">
              <el-button @click="itemViewDelete">删除</el-button>
            </el-button-group>
          </div>
        </div>
      </div>
      <div class="buttons">
        <el-dropdown :show-arrow="false" v-if="!isVanilla">
          <el-button type="primary" class="dropdown_button preset-button">
            <div>{{ presetDisplay }}</div>
            <el-icon class="el-icon--right"><arrow-down /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="item in presets" :key="item.name" @click="usePreset(item)">📦 {{ item.name
              }}</el-dropdown-item>
              <el-dropdown-item v-if="presets.length === 0 && customPresets.length === 0" disabled>暂无预设
              </el-dropdown-item>
              <el-dropdown-item v-if="customPresets.length > 0" divided disabled class="custom-preset-header">⭐ 我的预设
              </el-dropdown-item>
              <el-dropdown-item v-for="customPreset in customPresets" :key="customPreset.name"
                class="custom-preset-item" @click="loadCustomPreset(customPreset)">
                <span class="custom-preset-name">⭐ {{ customPreset.name }}</span>
                <span class="custom-preset-delete" title="删除" @click.stop="deleteCustomPreset(customPreset)">✖</span>
              </el-dropdown-item>
              <el-dropdown-item divided @click="saveCurrentAsPreset">💾 保存为预设…</el-dropdown-item>
              <el-dropdown-item v-if="uiSettings.submitPresetUrl" @click="submitPreset" divided>📫 预设投稿</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
        <el-button type="primary" @click="share" v-if="!isVanilla">👋分享列表</el-button>
        <el-button type="primary" @click="clickResetConfirm">🧹重置列表</el-button>
        <el-button type="primary" v-if="isMobile" @click="floatButtonVisible = !floatButtonVisible">👁️浮动按钮：{{
          floatButtonVisible ? "开" : "关" }}</el-button>
        <el-button type="primary" @click="toggleShuffleMode"
          :class="{ 'show-new-badge': shuffleNewBadgeVisible }">🎲打乱模式{{
            shuffleModeHint ? "" : shuffleMode ? "：开" : "：关"
          }}</el-button>
        <ImageUploader @upload="addLocalImages">📤{{ translate('本地图片') }}</ImageUploader>
        <el-button type="primary" v-if="isVanilla && chars.length > 0"
          @click="cardNameVisible = !cardNameVisible">🔠显示文字：{{
            cardNameVisible ? "开" : "关" }}</el-button>
        <el-dropdown :show-arrow="false" v-if="isVanilla && chars.length > 0">
          <el-button type="primary" class="dropdown_button">
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
          - 最后更新：{{ buildTime }}{{ isVanilla ? "" : " - " }}
          <a v-if="!isVanilla" :href="vanillaUrl">沙盒模式</a>
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

      <el-button v-if="shuffleMode" class="shuffle-float-button" type="primary" size="large" circle
        @click="handleShuffleClick">
        🎲
      </el-button>

      <SelectDialog v-model:visible="selectDialogVisible" :filtered-chars="filteredChars" :factions="factions"
        :filter-config="filterConfig" :translate="translate" :get-asset="asset" @select-char="select"
        @update-filter-config="handleUpdateFilterConfig" />

      <EditTierDialog v-model:visible="tierDialogVisible" :current-tier="currentTier"
        :predefine-colors="PREDEFINE_COLORS" @add-tier="handleAddTier" @remove-tier="handleRemoveTier"
        @update-tier="handleUpdateTier" />

      <FallbackCopyDialog v-model:visible="fallbackCopyDialogVisible" :copy-text="fallbackCopy" />
    </div>
  </main>
</template>

<script setup>
import * as InitData from "./data.js";
import * as VanillaData from "./data_v.js";
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from "vue";
import contenteditable from "vue-contenteditable";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowDown } from "@element-plus/icons-vue";
import ImageUploader from "./components/ImageUploader.vue";
import TierList from "./components/TierList.vue";
import AutoShrinkText from "./components/AutoShrinkText.vue";
import SelectDialog from "./components/SelectDialog.vue";
import EditTierDialog from "./components/EditTierDialog.vue";
import FallbackCopyDialog from "./components/FallbackCopyDialog.vue";
import { useTiers } from "./composables/useTiers.js";
import { useCharacters } from "./composables/useCharacters.js";
import { usePersistence } from "./composables/usePersistence.js";
import { usePlatform } from "./composables/usePlatform.js";
import { PREDEFINE_COLORS } from "./utils/constants.js";

const params = new URLSearchParams(window.location.search);
const isVanilla = InitData.namespace === "v" || params.has("v");
const { namespace, data, presets, lang, uiSettings } = isVanilla ? VanillaData : InitData;
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

const cardNameVisible = ref(true);
const vanillaCardScale = ref(100);
const vanillaCardWidth = ref(0);
const vanillaCardHeight = ref(0);
watch(vanillaCardScale, () => updateVanillaCardSize());
watch(cardNameVisible, () => updateVanillaCardSize());

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
  shuffleTiers,
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
const shuffleMode = ref(false);
const shuffleModeHint = ref(true);
const shuffleNewBadgeVisible = ref(
  namespace === "mjs" && localStorage.getItem(`${namespace}_shuffle_new_badge_dismissed`) !== "1",
);
const isMobile = ref(false);
const mediaQuery = window.matchMedia("(max-width: 767px)");
const forcePopover = ref(true);
const preset = ref();
const CUSTOM_PRESET_KEY = `${namespace}_tier_list_custom_presets`;
const MAX_CUSTOM_PRESETS = 20;
const customPresets = ref([]);
const readCustomPresets = () => {
  try {
    const parsed = JSON.parse(localStorage.getItem(CUSTOM_PRESET_KEY) || "[]");
    return Array.isArray(parsed)
      ? parsed.filter((p) => p && typeof p.name === "string" && typeof p.save === "string")
      : [];
  } catch (error) {
    console.warn("读取自定义预设失败", error);
    return [];
  }
};
const writeCustomPresets = () => {
  localStorage.setItem(CUSTOM_PRESET_KEY, JSON.stringify(customPresets.value));
};
customPresets.value = readCustomPresets();
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
  window.addEventListener("keydown", onItemViewKeydown);
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
  window.removeEventListener("keydown", onItemViewKeydown);
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

const ITEM_VIEW_MIN_SCALE = 0.25;
const ITEM_VIEW_MAX_SCALE = 1;

const itemViewChar = ref(null);
const itemViewOrigin = ref({ top: 0, left: 0, width: 0, height: 0 });
const itemViewStage = ref(null);
const itemViewTransition = ref(false);
const itemViewFadeOut = ref(false);
const itemViewClosing = ref(false);
// 缩放状态跨会话保留（仅缩放比例，固定以中心为原点）
const itemViewZoom = ref(0.4);

const itemViewWrapStyle = computed(() => {
  return { transform: `scale(${itemViewZoom.value})` };
});

const computeMorph = (stageEl, origin) => {
  const rect = stageEl.getBoundingClientRect();
  const ox = origin.left + origin.width / 2;
  const oy = origin.top + origin.height / 2;
  const cx = rect.left + rect.width / 2;
  const cy = rect.top + rect.height / 2;
  const scale = origin.width / rect.width;
  return `translate(${ox - cx}px, ${oy - cy}px) scale(${scale})`;
};

const openItemMenu = (e, char) => {
  const rect = e.currentTarget.getBoundingClientRect();
  itemViewOrigin.value = { top: rect.top, left: rect.left, width: rect.width, height: rect.height };
  itemViewChar.value = char;
  itemViewFadeOut.value = false;
  itemViewTransition.value = false;
  nextTick(() => {
    const el = itemViewStage.value;
    el.style.transform = computeMorph(el, itemViewOrigin.value);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        itemViewTransition.value = true;
        el.style.transform = "translate(0, 0) scale(1)";
      });
    });
  });
};

const finishItemView = () => {
  itemViewChar.value = null;
  itemViewClosing.value = false;
  itemViewFadeOut.value = false;
};

const closeItemView = (mode) => {
  if (!itemViewChar.value || itemViewClosing.value) return;
  itemViewClosing.value = true;
  if (mode === "delete") {
    removeFromList(itemViewChar.value);
  } else {
    const el = itemViewStage.value;
    el.style.transform = computeMorph(el, itemViewOrigin.value);
  }
  itemViewFadeOut.value = true;
  setTimeout(finishItemView, 320);
};

const itemViewDelete = () => {
  closeItemView("delete");
};

const onItemViewKeydown = (e) => {
  if (e.key === "Escape" && itemViewChar.value) {
    closeItemView("cancel");
  }
};

const onItemViewWheel = (e) => {
  const factor = e.deltaY < 0 ? 1.1 : 1 / 1.1;
  itemViewZoom.value = Math.min(
    ITEM_VIEW_MAX_SCALE,
    Math.max(ITEM_VIEW_MIN_SCALE, itemViewZoom.value * factor),
  );
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

const handleUpdateTier = (patch) => {
  Object.assign(currentTier.value, patch);
};

const handleUpdateFilterConfig = (patch) => {
  Object.assign(filterConfig.value, patch);
};

const isBuiltinPresetName = (name) => presets.some((p) => p.name === name);

const presetDisplay = computed(() => {
  if (!preset.value) {
    return "📦使用预设";
  }
  return isBuiltinPresetName(preset.value) ? preset.value : `⭐ ${preset.value}`;
});

const share = () => {
  const base = window.location.origin + window.location.pathname;
  if (preset.value && isBuiltinPresetName(preset.value)) {
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

const applyPreset = (save, name) => {
  loadList(save);
  if (preset.value !== name) {
    updatePresetTimestamp();
    preset.value = name;
  }
};

const usePreset = (newPreset) => {
  applyPreset(newPreset.save, newPreset.name);
};

const loadCustomPreset = (customPreset) => {
  applyPreset(customPreset.save, customPreset.name);
};

const doSaveCustomPreset = (name, save) => {
  const index = customPresets.value.findIndex((p) => p.name === name);
  if (index === -1) {
    customPresets.value.push({ name, save });
  } else {
    customPresets.value[index] = { name, save };
  }
  writeCustomPresets();
  msg("success", `已保存预设「${name}」`);
};

const saveCurrentAsPreset = () => {
  const result = saveList();
  if (result === null) {
    msg("warning", "列表为空，无法保存为预设");
    return;
  }
  if (customPresets.value.length >= MAX_CUSTOM_PRESETS) {
    msg("error", `自定义预设已达上限（${MAX_CUSTOM_PRESETS}条），请先删除部分预设`);
    return;
  }
  ElMessageBox.prompt("为当前排序命名，保存后可在预设下拉中随时加载。", "保存为预设", {
    confirmButtonText: "保存",
    cancelButtonText: "取消",
    inputPlaceholder: "请输入预设名称",
    inputValue: title.value || "",
    inputValidator: (value) => {
      const name = String(value).trim();
      if (!name) {
        return "预设名称不能为空";
      }
      if (name.length > 20) {
        return "预设名称不能超过 20 个字符";
      }
      if (isBuiltinPresetName(name)) {
        return "不能与内置预设重名";
      }
      return true;
    },
  })
    .then(({ value }) => {
      const name = String(value).trim();
      if (customPresets.value.some((p) => p.name === name)) {
        ElMessageBox.confirm(`已存在同名自定义预设「${name}」，是否覆盖？`, "覆盖预设", {
          confirmButtonText: "覆盖",
          confirmButtonType: "danger",
          cancelButtonText: "取消",
          type: "warning",
          center: true,
        })
          .then(() => {
            doSaveCustomPreset(name, result);
          })
          .catch(() => { });
      } else {
        doSaveCustomPreset(name, result);
      }
    })
    .catch(() => { });
};

const deleteCustomPreset = (customPreset) => {
  ElMessageBox.confirm(`确定删除自定义预设「${customPreset.name}」吗？`, "删除预设", {
    confirmButtonText: "删除",
    confirmButtonType: "danger",
    cancelButtonText: "取消",
    type: "warning",
    center: true,
  })
    .then(() => {
      customPresets.value = customPresets.value.filter((p) => p.name !== customPreset.name);
      if (preset.value === customPreset.name) {
        preset.value = undefined;
      }
      writeCustomPresets();
      msg("success", `已删除预设「${customPreset.name}」`);
    })
    .catch(() => { });
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

const handleShuffleClick = (event) => {
  shuffleTiers();
  event.currentTarget.querySelector("span").animate(
    [
      { transform: "translateY(-2px) rotate(0deg)" },
      { transform: "translateY(-13px) rotate(-90deg)" },
      { transform: "translateY(-2px) rotate(180deg)" },
      { transform: "translateY(-7px) rotate(270deg)" },
      { transform: "translateY(-2px) rotate(360deg)" },
    ],
    { duration: 600, easing: "ease-in-out" },
  );
};

const toggleShuffleMode = () => {
  if (shuffleNewBadgeVisible.value) {
    shuffleNewBadgeVisible.value = false;
    localStorage.setItem(`${namespace}_shuffle_new_badge_dismissed`, "1");
  }
  if (shuffleMode.value || !shuffleModeHint.value) {
    shuffleMode.value = !shuffleMode.value;
    return;
  }
  let hintText = "打乱模式开启后，页面下方会出现一个“🎲”按钮。<br/>点击该按钮会打乱所有已添加的项目，但每个栏目的项目数量保持不变。";
  if (namespace === "mjs") {
    hintText += "<br/>可以用来练习选将。";
  }
  ElMessageBox.confirm(
    hintText,
    "打乱模式",
    {
      confirmButtonText: "开启",
      cancelButtonText: "取消",
      type: "info",
      center: true,
      dangerouslyUseHTMLString: true,
    },
  )
    .then(() => {
      shuffleMode.value = true;
      shuffleModeHint.value = false;
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

const vanillaUrl = `${window.location.origin}${window.location.pathname}?v`;
</script>
