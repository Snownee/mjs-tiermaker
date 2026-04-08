// ==UserScript==
// @name         Rocom Wiki Exporter
// @namespace    http://snownee.com/
// @version      2026-04-07
// @description  try to take over the world!
// @author       Snownee
// @match        https://wiki.biligame.com/rocom/%E7%B2%BE%E7%81%B5%E5%9B%BE%E9%89%B4
// @icon         https://www.google.com/s2/favicons?sz=64&domain=biligame.com
// @grant        GM_registerMenuCommand
// ==/UserScript==

const exportData = () => {
  const dataList = [];
  $(".divsort").each((index, element) => {
    const data = {};
    data.name = element.querySelector(".rocom_prop_name a").title;
    const types = new Set();
    types.add(element.dataset.param1);
    types.add(element.dataset.param4);
    types.add(element.dataset.param5);
    data.类型 = [...types];
    data.属性 = element.dataset.param2.split(", ");
    data.异色 = element.dataset.param6 === "是" ? "有异色" : "无异色";
    data.img = element.querySelector('img').src;
    dataList.push(data);
  });
  downloadJSON(dataList);
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

(function () {
  "use strict";
  GM_registerMenuCommand("导出", function () {
    exportData();
  });
})();
