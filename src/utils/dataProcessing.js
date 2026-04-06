/**
 * Process raw character data by sorting and adding faction/name separation
 * @param {Object} data - Raw data object with values array
 * @returns {Array} Processed character array
 */
export const processData = (data) => {
  // Sort characters by name
  data.values.sort((a, b) => a.name.localeCompare(b.name));

  // Process each character
  data.values.forEach((value) => {
    // Split name into faction and character name
    const [faction, name] = value.name.split("/");
    value.faction = faction;
    value.name = name;
    value.selected = false;
  });

  return data.values;
};

/**
 * Get unique factions from character array
 * @param {Array} chars - Array of character objects
 * @returns {Array} Array of unique faction names
 */
export const getFactions = (chars) => {
  return [...new Set(chars.map((char) => char.faction))];
};
