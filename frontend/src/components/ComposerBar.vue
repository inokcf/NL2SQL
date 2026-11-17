<script setup lang="ts">
import { nextTick, onMounted, ref, watch } from "vue";
import { ArrowUp, Brain, Sparkles, Square } from "lucide-vue-next";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    streaming: boolean;
    canSend: boolean;
    placeholder?: string;
  }>(),
  {
    placeholder: "问一个电商数据问题，例如：统计华东地区本季度销售额…",
  },
);

const emit = defineEmits<{
  (event: "update:modelValue", value: string): void;
  (event: "submit"): void;
  (event: "stop"): void;
}>();

const textarea = ref<HTMLTextAreaElement | null>(null);

function resize() {
  const element = textarea.value;
  if (!element) return;
  element.style.height = "auto";
  element.style.height = `${Math.min(element.scrollHeight, 168)}px`;
}

function focus() {
  textarea.value?.focus();
}

function handleInput(event: Event) {
  emit("update:modelValue", (event.target as HTMLTextAreaElement).value);
}

function submit() {
  if (!props.streaming && props.canSend) emit("submit");
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== "Enter" || event.shiftKey) return;
  if (event.isComposing) return;
  event.preventDefault();
  submit();
}

watch(
  () => props.modelValue,
  () => nextTick(resize),
);

onMounted(resize);

defineExpose({ focus });
</script>

<template>
  <form class="composer" @submit.prevent="submit">
    <div class="composer-card">
      <span class="composer-mark" aria-hidden="true">
        <Sparkles :size="18" />
      </span>

      <textarea
        ref="textarea"
        :value="modelValue"
        :placeholder="placeholder"
        rows="1"
        aria-label="输入问数问题"
        @input="handleInput"
        @keydown="handleKeydown"
      />

      <button
        v-if="streaming"
        type="button"
        class="send-button is-stop"
        title="停止分析"
        aria-label="停止分析"
        @click="emit('stop')"
      >
        <Square :size="15" fill="currentColor" />
      </button>
      <button
        v-else
        type="submit"
        class="send-button"
        :disabled="!canSend"
        title="发送问题"
        aria-label="发送问题"
      >
        <ArrowUp :size="19" />
      </button>
    </div>

    <div class="composer-foot">
      <span class="shortcut-hint">
        <kbd>Enter</kbd> 发送
        <span class="hint-divider">·</span>
        <kbd>Shift</kbd> + <kbd>Enter</kbd> 换行
      </span>
      <span class="memory-hint">
        <Brain :size="12" />
        多轮记忆已开启
      </span>
    </div>
  </form>
</template>

<style scoped>
.composer {
  width: 100%;
  max-width: 940px;
  margin: 0 auto;
}

.composer-card {
  display: flex;
  align-items: flex-end;
  gap: 9px;
  padding: 8px;
  border: 1px solid var(--border-strong);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: var(--shadow-md);
  transition:
    border-color 160ms ease,
    box-shadow 160ms ease;
}

.composer-card:focus-within {
  border-color: rgba(16, 156, 137, 0.45);
  box-shadow:
    0 0 0 4px rgba(16, 156, 137, 0.09),
    var(--shadow-md);
}

.composer-mark {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(145deg, var(--brand-soft), #eef3ff);
  color: var(--brand-deep);
}

textarea {
  width: 100%;
  min-height: 48px;
  max-height: 168px;
  flex: 1;
  resize: none;
  border: 0;
  background: transparent;
  color: var(--text);
  font-size: 14.5px;
  line-height: 1.65;
  outline: none;
  padding: 11px 2px;
}

textarea::placeholder {
  color: var(--text-muted);
}

.send-button {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 auto;
  place-items: center;
  border: 0;
  border-radius: 13px;
  background: linear-gradient(135deg, #17ae99, #0c8b7b);
  box-shadow: 0 8px 18px rgba(16, 156, 137, 0.24);
  color: #fff;
  cursor: pointer;
  transition:
    transform 160ms ease,
    box-shadow 160ms ease,
    opacity 160ms ease,
    background 160ms ease;
}

.send-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 12px 22px rgba(16, 156, 137, 0.3);
}

.send-button:active:not(:disabled) {
  transform: translateY(0);
}

.send-button:disabled {
  cursor: not-allowed;
  opacity: 0.38;
  box-shadow: none;
}

.send-button.is-stop {
  border: 1px solid rgba(217, 82, 82, 0.18);
  background: var(--danger-soft);
  box-shadow: none;
  color: var(--danger);
}

.send-button.is-stop:hover {
  background: #fbdede;
  box-shadow: none;
}

.composer-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 6px 0;
  color: var(--text-muted);
  font-size: 10px;
}

.shortcut-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.hint-divider {
  margin: 0 2px;
  opacity: 0.5;
}

kbd {
  display: inline-block;
  min-width: 16px;
  padding: 1px 4px;
  border: 1px solid var(--border);
  border-bottom-width: 2px;
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-secondary);
  font-family: var(--font-sans);
  font-size: 9px;
  line-height: 1.35;
  text-align: center;
}

.memory-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--brand-deep);
  font-weight: 550;
  white-space: nowrap;
}

@media (max-width: 640px) {
  .composer-card {
    gap: 6px;
    padding: 7px;
    border-radius: 16px;
  }

  .composer-mark {
    display: none;
  }

  textarea {
    min-height: 44px;
    padding-left: 8px;
    font-size: 14px;
  }

  .send-button {
    width: 40px;
    height: 40px;
  }

  .shortcut-hint {
    display: none;
  }

  .composer-foot {
    justify-content: flex-end;
  }
}
</style>
