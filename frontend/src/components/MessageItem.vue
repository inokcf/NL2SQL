<script setup lang="ts">
import { computed, ref } from "vue";
import {
  AlertCircle,
  Brain,
  Check,
  Copy,
  Database,
  Sparkles,
  UserRound,
} from "lucide-vue-next";

import ResultTable from "./ResultTable.vue";
import StepTimeline from "./StepTimeline.vue";
import { copyText, formatTime, toClipboardText } from "../lib/format";
import type { ChatMessage } from "../types/agent";

const props = defineProps<{
  message: ChatMessage;
}>();

const isUser = computed(() => props.message.role === "user");
const time = computed(() => formatTime(props.message.createdAt));
const copied = ref(false);

const resolvedDifferent = computed(() => {
  const resolved = props.message.resolvedQuery?.trim();
  return Boolean(resolved && resolved !== props.message.content.trim());
});

const showSqlBlock = computed(() => {
  const sql = props.message.sql?.trim();
  if (!sql) return false;
  return !props.message.content.includes(sql.slice(0, 60));
});

const showSteps = computed(
  () =>
    !isUser.value &&
    (Boolean(props.message.steps?.length) ||
      props.message.status === "streaming"),
);

async function copyMessage() {
  const value = props.message.result ?? props.message.content;
  await copyText(toClipboardText(value));
  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1400);
}
</script>

<template>
  <article class="message" :class="isUser ? 'message--user' : 'message--assistant'">
    <div v-if="!isUser" class="avatar avatar--assistant" aria-hidden="true">
      <Sparkles :size="16" />
    </div>

    <div class="message-body">
      <div v-if="!isUser" class="message-meta">
        <span class="assistant-name">数据分析助手</span>
        <span v-if="message.fromHistory" class="history-tag">历史会话</span>
        <span class="meta-time">{{ time }}</span>
      </div>

      <div class="bubble" :class="isUser ? 'bubble--user' : 'bubble--assistant'">
        <p class="message-text">{{ message.content }}</p>

        <div v-if="isUser && resolvedDifferent" class="resolved-hint">
          <Brain :size="13" />
          <span>结合上下文：{{ message.resolvedQuery }}</span>
        </div>

        <div v-if="message.error" class="error-box">
          <AlertCircle :size="15" />
          <span>{{ message.error }}</span>
        </div>

        <StepTimeline
          v-if="showSteps"
          :steps="message.steps ?? []"
          :status="message.status"
        />

        <details v-if="!isUser && showSqlBlock" class="sql-block">
          <summary>
            <Database :size="14" />
            查看本轮 SQL
          </summary>
          <pre>{{ message.sql }}</pre>
        </details>

        <ResultTable
          v-if="!isUser && message.result !== undefined"
          :data="message.result"
        />

        <div v-if="!isUser" class="bubble-actions">
          <button
            type="button"
            class="icon-button copy-button"
            :title="copied ? '已复制' : '复制内容'"
            :aria-label="copied ? '已复制' : '复制内容'"
            @click="copyMessage"
          >
            <Check v-if="copied" :size="14" />
            <Copy v-else :size="14" />
          </button>
        </div>
      </div>

      <div v-if="isUser" class="user-meta">
        <span class="meta-time">{{ time }}</span>
        <span class="avatar avatar--user" aria-hidden="true">
          <UserRound :size="14" />
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.message {
  display: flex;
  gap: 10px;
  animation: message-in 240ms ease both;
}

.message--user {
  justify-content: flex-end;
}

.message-body {
  min-width: 0;
  max-width: min(860px, 100%);
}

.message--user .message-body {
  display: flex;
  max-width: min(76%, 700px);
  flex-direction: column;
  align-items: flex-end;
}

.avatar {
  display: grid;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 10px;
}

.avatar--assistant {
  width: 32px;
  height: 32px;
  margin-top: 2px;
  background: linear-gradient(145deg, var(--brand-soft), #eef3ff);
  box-shadow: var(--shadow-xs);
  color: var(--brand-deep);
}

.avatar--user {
  width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(145deg, #19b09b, #0c8b7b);
  color: #fff;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 6px;
  padding-left: 2px;
}

.assistant-name {
  color: var(--text);
  font-size: 12px;
  font-weight: 650;
}

.history-tag {
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--sky-soft);
  color: #3c6fca;
  font-size: 9px;
  font-weight: 650;
}

.meta-time {
  color: var(--text-muted);
  font-size: 10px;
}

.bubble {
  position: relative;
  padding: 13px 16px;
}

.bubble--assistant {
  border: 1px solid var(--border);
  border-radius: 4px 18px 18px 18px;
  background: var(--surface);
  box-shadow: var(--shadow-sm);
}

.bubble--user {
  border-radius: 18px 4px 18px 18px;
  background: linear-gradient(140deg, #16aa95, #0d8b7b);
  box-shadow: 0 10px 24px rgba(13, 139, 123, 0.2);
  color: #fff;
}

.message-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-box {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  margin-top: 11px;
  padding: 9px 11px;
  border: 1px solid rgba(217, 82, 82, 0.17);
  border-radius: 10px;
  background: var(--danger-soft);
  color: #b53f3f;
  font-size: 12px;
  line-height: 1.55;
}

.error-box svg {
  flex: 0 0 auto;
  margin-top: 1px;
}

.resolved-hint {
  display: flex;
  align-items: flex-start;
  gap: 5px;
  margin-top: 9px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.16);
  color: rgba(255, 255, 255, 0.68);
  font-size: 11px;
  line-height: 1.55;
}

.resolved-hint svg {
  flex: 0 0 auto;
  margin-top: 2px;
}

.bubble-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 4px;
  margin-bottom: -4px;
}

.copy-button {
  width: 26px;
  height: 26px;
  opacity: 0;
  color: var(--text-muted);
}

.bubble--assistant:hover .copy-button,
.copy-button:focus-visible {
  opacity: 1;
}

@media (hover: none) {
  .copy-button {
    opacity: 0.72;
  }
}

.sql-block {
  margin-top: 12px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface-soft);
}

.sql-block summary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 11px;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  list-style: none;
  user-select: none;
}

.sql-block summary::-webkit-details-marker {
  display: none;
}

.sql-block summary svg {
  color: var(--brand);
}

.sql-block pre {
  max-height: 240px;
  margin: 0;
  padding: 0 11px 11px;
  overflow: auto;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.user-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 6px;
  padding-right: 2px;
}

.message--user .meta-time {
  color: var(--text-muted);
}

@media (max-width: 640px) {
  .message--user .message-body {
    max-width: 88%;
  }

  .bubble {
    padding: 11px 13px;
  }

  .message-text {
    font-size: 13.5px;
  }
}
</style>
