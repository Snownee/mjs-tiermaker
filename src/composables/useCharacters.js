import { ref, watch } from "vue";

/**
 * Composable for managing character data and filtering
 * @param {Object} data - Raw character data
 * @param {Object} uiSettings - UI settings for extra filters
 * @returns {Object} Character management functions and reactive state
 */
export const useCharacters = (data, uiSettings) => {
  const filteredChars = ref([]);
  const { chars, factions, filterConfig } = processData(data, uiSettings);

  const filterChars = () => {
    let newChars = chars.value.filter((char) =>
      char.selected
        ? filterConfig.value.showAdded
        : filterConfig.value.showNotAdded,
    );
    if (filterConfig.value.factionFilter.length > 0) {
      newChars = newChars.filter((char) =>
        filterConfig.value.factionFilter.includes(char.faction),
      );
    }
    Object.values(filterConfig.value.extraFilters).forEach((filter) => {
      if (filter.value == undefined || filter.value.length === 0) {
        return;
      }

      newChars = newChars.filter((char) => {
        const charValue = char[filter.key];
        if (!charValue) {
          return false;
        }
        if (filter.multiple && Array.isArray(charValue)) {
          return charValue.some((value) => filter.value.includes(value));
        } else {
          return filter.value.includes(charValue);
        }
      });
    });
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

const processData = (data, uiSettings) => {
  // Sort characters by name
  data.values.sort((a, b) => a.name.localeCompare(b.name));

  // Process each character
  data.values.forEach((value) => {
    // Split name into faction and character name
    const [faction, name] = value.name.split("/");
    value.faction = faction;
    value.name = name;
    value.selected = false;
    if (uiSettings.nameFormatter) {
      value.displayName = uiSettings.nameFormatter(value.name);
    }
  });

  const chars = ref(data.values);
  const factions = ref([...new Set(data.values.map((char) => char.faction))]);
  const extraFilters = uiSettings.extraFilters || {};
  const showFactionFilter = !(uiSettings.hideFactionFilter || false);
  Object.entries(extraFilters).forEach(([key, filter]) => {
    filter.key = key;
    filter.value = [];
    if (!filter.options) {
      const options = new Set();
      chars.value.forEach((char) => {
        const charValue = char[key];
        if (charValue) {
          if (Array.isArray(charValue)) {
            charValue.forEach((value) => options.add(value));
          } else {
            options.add(charValue);
          }
        }
      });
      filter.options = [...options].sort();
    }
  });

  const filterConfig = ref({
    showNotAdded: true,
    showAdded: false,
    factionFilter: [],
    showFactionFilter,
    extraFilters,
  });

  return { chars, factions, filterConfig };
};
