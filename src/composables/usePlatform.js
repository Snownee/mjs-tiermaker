export const usePlatform = (hostname) => {
  let platform = "github";
  let authorUrl = "https://github.com/Snownee/mjs-tiermaker";
  if (hostname.includes("tap")) {
    platform = "taptap";
    authorUrl = "https://www.taptap.cn/user/757224223";
  } else if (hostname.includes("bili")) {
    platform = "bilibili";
    authorUrl = "https://space.bilibili.com/6939567";
  }
  return {
    platform,
    authorUrl,
  };
};
