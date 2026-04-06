import { ref } from "vue";
import { INIT_TIERS, PREDEFINE_COLORS, MAX_TIERS } from "../utils/constants.js";

/**
 * Composable for managing tier list state and operations
 * @param {Array} chars - Array of character objects
 * @param {Function} msg - Message function for notifications
 * @returns {Object} Tier management functions and reactive state
 */
export const useTiers = (chars, msg) => {
  const tiers = ref(JSON.parse(JSON.stringify(INIT_TIERS)));
  let lastTimeUsePreset = Date.now();

  /**
   * Reset the tier list to initial state
   */
  const resetList = () => {
    tiers.value = JSON.parse(JSON.stringify(INIT_TIERS));
    chars.value.forEach((char) => (char.selected = false));
  };

  /**
   * Add a new tier above or below the specified tier
   * @param {Object} tier - The reference tier
   * @param {string} position - 'up' or 'down'
   */
  const addTier = (tier, position) => {
    if (tiers.value.length >= MAX_TIERS) {
      msg("error", "已达到栏目数量上限");
      return;
    }

    const index = tiers.value.findIndex((t) => t.id === tier.id);
    const colorIndex = PREDEFINE_COLORS.indexOf(tier.color);
    const color = PREDEFINE_COLORS[(colorIndex + 1) % PREDEFINE_COLORS.length];

    const newTier = {
      id: Date.now(),
      name: "New",
      color: color,
      items: [],
    };

    if (position === "up") {
      tiers.value.splice(index, 0, newTier);
    } else {
      tiers.value.splice(index + 1, 0, newTier);
    }
  };

  /**
   * Remove a tier with animation
   * @param {Object} tier - The tier to remove
   */
  const removeTier = (tier) => {
    if (tiers.value.length === 1) {
      msg("error", "至少保留一个等级");
      return;
    }

    tier.deleting = true;

    setTimeout(() => {
      tier.items.forEach((char) => (char.selected = false));
      const index = tiers.value.findIndex((t) => t.id === tier.id);
      tiers.value.splice(index, 1);
    }, 300);
  };

  /**
   * Add a character to a specific tier
   * @param {Object} char - The character to add
   * @param {Object} tier - The target tier
   */
  const addToList = (char, tier) => {
    char.selected = true;
    tier.items.push(char);
  };

  /**
   * Remove a character from all tiers
   * @param {Object} char - The character to remove
   */
  const removeFromList = (char) => {
    char.selected = false;
    tiers.value.forEach((tier) => {
      tier.items = tier.items.filter((item) => item.id !== char.id);
    });
  };

  /**
   * Update the preset timestamp to track changes
   */
  const updatePresetTimestamp = () => {
    lastTimeUsePreset = Date.now();
  };

  /**
   * Check if enough time has passed since last preset use
   * @returns {boolean} True if more than 500ms have passed
   */
  const shouldUpdatePreset = () => {
    return Date.now() - lastTimeUsePreset > 500;
  };

  return {
    tiers,
    resetList,
    addTier,
    removeTier,
    addToList,
    removeFromList,
    updatePresetTimestamp,
    shouldUpdatePreset,
  };
};
