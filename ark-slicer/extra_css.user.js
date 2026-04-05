// ==UserScript==
// @name         Arknights Extra CSS
// @namespace    http://snownee.com/
// @version      2026-04-04
// @description  try to take over the world!
// @author       Snownee
// @match        https://wiki.biligame.com/arknights/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=biligame.com
// @grant        GM_addStyle
// ==/UserScript==

// https://marketplace.visualstudio.com/items?itemName=Tobermory.es6-string-html
const css = /* css */ `

#bodyContent {
    background: green;
}

.operator-handbook-item-label-container {
    display: none !important;
}

.operator-handbook-item-wrapper {
    margin-bottom: 30px;
    background: white;
}

.operator-handbook-item-wrapper::before {
    content: '';
    position: absolute;
    height: 100%;
    top: 0;
    bottom: 0;
    background: green;
    z-index: 1;
    width: 8px;
    left: -8px;
}

.operator-handbook-item-wrapper::after {
    content: '';
    position: absolute;
    height: 100%;
    top: 0;
    bottom: 0;
    background: green;
    z-index: 1;
    width: 8px;
    right: -8px;
}

.operator-handbook-item-name {
    transform: translateY(30px);
    background: white;
    color: black !important;
    padding: 0 5px !important;
}

.wiki-nav {
    display: none !important;
}

`;

(function () {
    'use strict';

    GM_addStyle(css);
})();