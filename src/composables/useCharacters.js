import { ref, watch } from "vue";
import { processData, getFactions } from "../utils/dataProcessing.js";

/**
 * Composable for managing character data and filtering
 * @param {Object} data - Raw character data
 * @returns {Object} Character management functions and reactive state
 */
export const useCharacters = (data) => {
  const chars = ref(processData(data));
  const factions = ref(getFactions(chars.value));
  const filteredChars = ref([]);

  // Centralized filter configuration object
  const filterConfig = ref({
    showNotAdded: true,
    showAdded: false,
    factionFilter: "",
  });

  /**
   * Filter characters based on current filters
   */
  const filterChars = () => {
    const newChars = chars.value.filter(
      (char) =>
        (char.selected ? filterConfig.value.showAdded : filterConfig.value.showNotAdded) &&
        (char.faction === filterConfig.value.factionFilter ||
          filterConfig.value.factionFilter === "" ||
          filterConfig.value.factionFilter === undefined),
    );
    filteredChars.value = newChars;
  };

  // Watch for filter changes
  watch(filterConfig, filterChars, { deep: true });

  /**
   * Select or deselect a character
   * @param {Object} char - The character to toggle
   * @param {Object} currentTier - The current tier for adding
   * @param {Function} addToList - Function to add to tier
   * @param {Function} removeFromList - Function to remove from tiers
   */
  const select = (char, currentTier, addToList, removeFromList) => {
    if (char.selected) {
      removeFromList(char);
    } else {
      addToList(char, currentTier);
    }
  };

  return {
    chars,
    factions,
    filteredChars,
    filterConfig,
    filterChars,
    select,
  };
};
