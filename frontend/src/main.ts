/**
 * Vue 应用入口
 * 挂载根组件并加载全局设计变量与基础样式。
 */
import { createApp } from "vue";

import App from "./App.vue";
import "./styles/main.css";

createApp(App).mount("#app");
