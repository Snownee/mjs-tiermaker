// Predefined colors for tiers
export const PREDEFINE_COLORS = [
  "#ff7f7f",
  "#ffbf7f",
  "#ffdf7f",
  "#ffff7f",
  "#bfff7f",
  "#7fff7f",
  "#7fffff",
  "#7fbfff",
  "#7f7fff",
];

// Initial tier configuration
export const INIT_TIERS = [
  { id: 1, name: "夯", color: PREDEFINE_COLORS[0], items: [] },
  { id: 2, name: "顶级", color: PREDEFINE_COLORS[1], items: [] },
  { id: 3, name: "人上人", color: PREDEFINE_COLORS[2], items: [] },
  { id: 4, name: "NPC", color: PREDEFINE_COLORS[3], items: [] },
  { id: 5, name: "拉完了", color: PREDEFINE_COLORS[4], items: [] },
];

// Maximum number of tiers allowed
export const MAX_TIERS = 14;
