/**
 * Calculate the contrast color (black or white) for a given hex color
 * @param {string} hexColor - The hex color string (e.g., '#ff7f7f')
 * @returns {string} '#000000' for light backgrounds, '#FFFFFF' for dark backgrounds
 */
export const getContrastColor = (hexColor) => {
  // Remove # and handle shorthand hex (e.g., #03F -> #0033FF)
  let hex = hexColor.replace("#", "");

  if (hex.length === 3) {
    hex = hex
      .split("")
      .map((char) => char + char)
      .join("");
  }

  // Using substring(start, end) instead of the deprecated substr()
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);

  // Calculate brightness using the ITU-R BT.709 coefficients
  const brightness = (r * 212.6 + g * 715.2 + b * 72.2) / 1000;

  return brightness > 128 ? "#000000" : "#FFFFFF";
};
