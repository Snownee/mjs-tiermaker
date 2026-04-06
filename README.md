# MJS Tier Maker

A Vue.js application for creating tier lists for characters from various factions in the MJS (likely a game or series). Supports multiple data sources (MJS and ARK) and allows users to drag and drop characters into customizable tiers.

## Features

- Drag and drop characters into tiers
- Customizable tier names and colors
- Preset configurations
- Shareable tier lists via URL
- Mobile responsive design
- Multiple data sources (MJS and ARK)

## Recommended IDE Setup

[VS Code](https://code.visualstudio.com/) + [Vue (Official)](https://marketplace.visualstudio.com/items?itemName=Vue.volar) (and disable Vetur).

## Recommended Browser Setup

- Chromium-based browsers (Chrome, Edge, Brave, etc.):
  - [Vue.js devtools](https://chromewebstore.google.com/detail/vuejs-devtools/nhdogjmejiglipccpnnnanhbledajbpd)
  - [Turn on Custom Object Formatter in Chrome DevTools](http://bit.ly/object-formatters)
- Firefox:
  - [Vue.js devtools](https://addons.mozilla.org/en-US/firefox/addon/vue-js-devtools/)
  - [Turn on Custom Object Formatter in Firefox DevTools](https://fxdx.dev/firefox-devtools-custom-object-formatters/)

## Project Setup

```sh
npm install
```

### Switch Data Source

The project supports two data sources: MJS and ARK.

```sh
# Switch to MJS data
npm run set_mjs

# Switch to ARK data
npm run set_ark
```

### Compile and Hot-Reload for Development

```sh
npm run dev
```

### Compile and Minify for Production

```sh
npm run build
```

## Project Structure

- `src/` - Main source code
  - `components/` - Vue components
  - `assets/` - Images and styles
- `src_mjs/` - MJS data source
- `src_ark/` - ARK data source
- `ark-slicer/` and `mjs-slicer/` - Python tools for processing images
- `set.js` - Script to switch between data sources

## Customize configuration

See [Vite Configuration Reference](https://vite.dev/config/).
