<template>
    <div ref="container" class="shrink-container">
        <svg v-if="isOverflowing" :viewBox="`0 0 ${textWidth} ${textHeight}`" width="100%" height="100%"
            preserveAspectRatio="none" class="svg-text">
            <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" :font-size="fontSize"
                :font-family="fontFamily">
                {{ text }}
            </text>
        </svg>

        <span v-else ref="measureSpan" class="normal-text">
            {{ text }}
        </span>
    </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch } from 'vue';

const props = defineProps({
    text: { type: String, required: true },
    fontSize: { type: String, default: '13px' },
    fontFamily: { type: String, default: 'sans-serif' },
    tolerance: { type: Number, default: 4 }
});

const container = ref(null);
const measureSpan = ref(null);
const isOverflowing = ref(false);
const textWidth = ref(0);
const textHeight = ref(0);

const checkOverflow = () => {
    if (!container.value || !measureSpan.value) return;

    const containerWidth = container.value.offsetWidth;
    const contentWidth = measureSpan.value.offsetWidth;
    const contentHeight = measureSpan.value.offsetHeight;

    if (contentWidth > containerWidth + props.tolerance) {
        isOverflowing.value = true;
        textWidth.value = contentWidth;
        textHeight.value = contentHeight;
    } else {
        isOverflowing.value = false;
    }
};

onMounted(() => {
    checkOverflow();
    // 可选：监听窗口大小变化
    window.addEventListener('resize', checkOverflow);
});

// 当文字内容改变时重新检测
watch(() => props.text, () => {
    isOverflowing.value = false; // 先重置以便重新测量
    nextTick(checkOverflow);
});
</script>

<style scoped>
/* .shrink-container {} */

.svg-text {
    width: 100%;
}

.normal-text {
    display: inline-block;
}
</style>