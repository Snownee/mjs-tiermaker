import { load, save } from "../save.js";

/**
 * Composable for handling data persistence (save/load)
 * @param {Object} tiers - Reactive tiers reference
 * @param {Object} chars - Reactive characters reference
 * @param {Object} title - Reactive title reference
 * @param {Object} subtitle - Reactive subtitle reference
 * @param {string} namespace - App namespace for localStorage
 * @param {Function} msg - Message function for notifications
 * @returns {Object} Persistence functions
 */
export const usePersistence = (
  tiers,
  chars,
  title,
  subtitle,
  namespace,
  msg,
) => {
  /**
   * Save the current tier list to a compressed string
   * @param {boolean} allowEmpty - Whether to allow saving empty lists
   * @returns {string|null} Compressed data string or null if empty and not allowed
   */
  const saveList = (allowEmpty = false) => {
    if (!allowEmpty && tiers.value.every((tier) => tier.items.length === 0)) {
      return null;
    }

    const tiersData = tiers.value.map((tier) => ({
      name: tier.name,
      color: tier.color,
      items: tier.items.map((item) => item.id),
    }));

    return save({
      title: title.value || "",
      subtitle: subtitle.value || "",
      tiers: tiersData,
    });
  };

  /**
   * Load tier list data from saved data
   * @param {string|Object} saveData - The data to load (string or parsed object)
   * @returns {boolean} True if loaded successfully
   */
  const loadList = (saveData) => {
    if (typeof saveData === "string") {
      try {
        saveData = load(saveData);
      } catch (error) {
        saveData = { error: 3 };
      }

      if (saveData.error) {
        msg("error", "读取数据时出错");
        return false;
      }
    }

    // Reset character selections
    chars.value.forEach((char) => (char.selected = false));

    // Update title and subtitle
    title.value = saveData.title;
    subtitle.value = saveData.subtitle;

    // Process tiers and assign IDs
    const newTiers = saveData.tiers.map((tier) => {
      tier.items = tier.items
        .map((itemId) => {
          const char = chars.value.find((c) => c.id === itemId);
          if (char) {
            char.selected = true;
            return char;
          }
          return null;
        })
        .filter((item) => item !== null);
      return tier;
    });

    // Assign sequential IDs to tiers
    let nextId = 1;
    for (const tier of newTiers) {
      tier.id = nextId++;
    }

    tiers.value = newTiers;
    return true;
  };

  /**
   * Save current state to localStorage
   * @param {boolean} allowEmpty - Whether to allow saving empty lists
   */
  const saveToLocalStorage = (allowEmpty = false) => {
    const result = saveList(allowEmpty);
    if (result) {
      localStorage.setItem(`${namespace}_tier_list_tiers`, result);
    }
  };

  /**
   * Load state from localStorage
   * @returns {boolean} True if loaded successfully
   */
  const loadFromLocalStorage = () => {
    const saveData = localStorage.getItem(`${namespace}_tier_list_tiers`);
    if (saveData && loadList(saveData)) {
      return true;
    }
    return false;
  };

  return {
    saveList,
    loadList,
    saveToLocalStorage,
    loadFromLocalStorage,
  };
};
