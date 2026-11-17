<script setup lang="ts">
import {
  ArrowUpRight,
  Brain,
  Database,
  Search,
  Sparkles,
} from "lucide-vue-next";

import type { ExamplePrompt } from "../lib/examples";

defineProps<{
  examples: ExamplePrompt[];
}>();

const emit = defineEmits<{
  (event: "use", text: string): void;
}>();

const features = [
  { label: "混合检索", icon: Search },
  { label: "多轮记忆", icon: Brain },
  { label: "SQL 闭环", icon: Database },
];
</script>

<template>
  <div class="empty-state">
    <div class="hero">
      <div class="hero-badge">
        <span class="badge-icon" aria-hidden="true">
          <Sparkles :size="14" />
        </span>
        AI 数据助手
      </div>

      <h1>
        用一句话，问清你的
        <span class="accent">经营数据</span>
      </h1>
      <p class="hero-copy">
        连接电商数仓，自动完成字段召回、指标理解与 SQL 生成。
        支持多轮追问和长期记忆，越聊越懂你的分析习惯。
      </p>

      <div class="feature-row">
        <span v-for="feature in features" :key="feature.label" class="feature-chip">
          <component :is="feature.icon" :size="14" aria-hidden="true" />
          {{ feature.label }}
        </span>
      </div>
    </div>

    <section class="prompt-section">
      <div class="prompt-head">
        <span>试试这样问</span>
        <span class="prompt-hint">点击填入输入框</span>
      </div>

      <div class="prompt-grid">
        <button
          v-for="example in examples"
          :key="example.text"
          type="button"
          class="prompt-card"
          @click="emit('use', example.text)"
        >
          <span class="prompt-icon" aria-hidden="true">
            <component :is="example.icon" :size="18" />
          </span>
          <span class="prompt-body">
            <span class="prompt-label">{{ example.label }}</span>
            <span class="prompt-text">{{ example.text }}</span>
          </span>
          <ArrowUpRight class="prompt-arrow" :size="16" aria-hidden="true" />
        </button>
      </div>
    </section>

    <p class="empty-foot">
      由 FastAPI · LangGraph · Qdrant 驱动
    </p>
  </div>
</template>

<style scoped>
.empty-state {
  width: 100%;
  max-width: 960px;
  margin: 0 auto;
  padding: 64px 28px 40px;
}

.hero {
  max-width: 740px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 22px;
  padding: 5px 12px 5px 5px;
  border: 1px solid rgba(16, 156, 137, 0.16);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-xs);
  color: var(--brand-deep);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.badge-icon {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 999px;
  background: var(--brand-soft);
}

.hero h1 {
  max-width: 680px;
  margin: 0;
  color: var(--text);
  font-size: clamp(34px, 5vw, 54px);
  font-weight: 750;
  letter-spacing: -0.045em;
  line-height: 1.12;
  text-wrap: balance;
}

.hero h1 .accent {
  background: linear-gradient(120deg, #0d9b87 10%, #31b9a3 55%, #4d8df7 110%);
  background-clip: text;
  -webkit-background-clip: text;
  color: transparent;
}

.hero-copy {
  max-width: 620px;
  margin: 20px 0 0;
  color: var(--text-secondary);
  font-size: 15px;
  line-height: 1.85;
}

.feature-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 24px;
}

.feature-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 11px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.6);
  color: var(--text-secondary);
  font-size: 11px;
  font-weight: 600;
}

.feature-chip svg {
  color: var(--brand);
}

.prompt-section {
  margin-top: 52px;
}

.prompt-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  padding: 0 2px;
}

.prompt-head > span:first-child {
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
}

.prompt-hint {
  color: var(--text-muted);
  font-size: 11px;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.prompt-card {
  display: flex;
  min-height: 96px;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.72);
  box-shadow: var(--shadow-xs);
  cursor: pointer;
  text-align: left;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    box-shadow 180ms ease,
    background 180ms ease;
}

.prompt-card:hover {
  transform: translateY(-2px);
  border-color: rgba(16, 156, 137, 0.22);
  background: var(--surface);
  box-shadow: var(--shadow-md);
}

.prompt-card:active {
  transform: translateY(0);
}

.prompt-icon {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 11px;
  background: linear-gradient(145deg, var(--brand-soft), #eef4ff);
  color: var(--brand-deep);
}

.prompt-body {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.prompt-label {
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.prompt-text {
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.55;
}

.prompt-arrow {
  flex: 0 0 auto;
  margin-top: 2px;
  color: var(--text-muted);
  opacity: 0;
  transform: translate(-3px, 3px);
  transition:
    opacity 180ms ease,
    transform 180ms ease,
    color 180ms ease;
}

.prompt-card:hover .prompt-arrow {
  color: var(--brand);
  opacity: 1;
  transform: translate(0, 0);
}

.empty-foot {
  margin: 34px 0 0;
  color: var(--text-muted);
  font-size: 10px;
  letter-spacing: 0.1em;
  text-align: center;
  text-transform: uppercase;
}

@media (max-width: 720px) {
  .empty-state {
    padding: 40px 18px 28px;
  }

  .hero h1 {
    font-size: 34px;
  }

  .prompt-section {
    margin-top: 36px;
  }

  .prompt-grid {
    grid-template-columns: 1fr;
  }
}
</style>
