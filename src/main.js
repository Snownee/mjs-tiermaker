import { createApp } from "vue";
import "@/main.css";
import "@/assets/special.css";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import "normalize.css/normalize.css";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import App from "./App.vue";

const app = createApp(App);
app.use(ElementPlus, {
  locale: zhCn,
});

app.mount("#app");
