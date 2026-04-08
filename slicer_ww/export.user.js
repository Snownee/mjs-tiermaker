// ==UserScript==
// @name         WW Wiki Exporter
// @namespace    http://snownee.com/
// @version      2026-04-07
// @description  try to take over the world!
// @author       Snownee
// @match        https://wiki.kurobbs.com/mc/catalogue/list*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=kurobbs.com
// @grant        GM_registerMenuCommand
// @grant        GM_addStyle
// ==/UserScript==

const exportData = () => {
  const data =
    document.querySelector("#app").__vue_app__.config.globalProperties.$pinia
      .state._rawValue.useCatalogueStore.page;
  const tagListData = data.tagTree.children;
  const tags = {};
  for (const tag of tagListData) {
    tags[tag.id] = stripTag(tag);
    for (const child of tag.children) {
      tags[child.id] = stripTag(child);
    }
  }
  const cards = {};
  for (const card of data.cards) {
    const cardData = { name: card.name };
    for (const tagId of card.content.relateTagIds) {
      const tagValue = tags[tagId].name;
      const tagKey = tags[tags[tagId].parentId].name;
      if (tagKey === "稀有度") {
        cardData[tagKey] = tagValue;
      } else {
        const tagValues = cardData[tagKey] || [];
        tagValues.push(tagValue);
        cardData[tagKey] = tagValues;
      }
    }
    cards[card.name] = cardData;
  }
  downloadJSON({ tags, cards });
};

const stripTag = (data) => {
  return {
    id: data.id,
    name: data.name,
    parentId: data.parentId,
  };
};

const downloadJSON = (data) => {
  // 将对象转换为字符串
  const jsonString = JSON.stringify(data, null, 4);

  // 创建 Blob 对象 (二进制大对象)
  const blob = new Blob([jsonString], { type: "application/json" });

  // 创建一个隐藏的下载链接
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "data_export.json"; // 指定下载的文件名

  // 触发点击并移除临时元素
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);

  // 释放 URL 对象，节省内存
  URL.revokeObjectURL(link.href);

  console.log("JSON 文件已导出");
};

// https://marketplace.visualstudio.com/items?itemName=Tobermory.es6-string-html
const css = /* css */ `
.entry-teaser,
.feedback-aside-layout,
.ant-back-top {
    display: none !important;
}

.glossary-catalog {
    background: green !important;
}

.invalid-status * {
    border-radius: 0 !important;
}

.card-footer {
    background-color: green !important;
    border: none !important;
}

.card-footer-inner span {
    color: white !important;
    background: black !important;
    padding: 4px 4px !important;
}
`;

(function () {
  "use strict";
  GM_registerMenuCommand("导出", function () {
    exportData();
  });
  GM_registerMenuCommand("隐藏表单", function () {
    GM_addStyle(/* css */ `
        .catalog-name,
        .catalog-side-lv-cont,
        .catalog-tags {
            display: none !important;
        }
    `);
  });
  GM_addStyle(css);
})();
