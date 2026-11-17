<script setup lang="ts">
import { AlertTriangle } from "lucide-vue-next";

withDefaults(
  defineProps<{
    open: boolean;
    title: string;
    message: string;
    confirmText?: string;
    danger?: boolean;
  }>(),
  {
    confirmText: "确认",
    danger: false,
  },
);

const emit = defineEmits<{
  (event: "confirm"): void;
  (event: "cancel"): void;
}>();
</script>

<template>
  <Teleport to="body">
    <Transition name="dialog">
      <div
        v-if="open"
        class="dialog-root"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        @click.self="emit('cancel')"
      >
        <div class="dialog-card">
          <span class="dialog-icon" :class="{ 'is-danger': danger }" aria-hidden="true">
            <AlertTriangle :size="20" />
          </span>
          <div class="dialog-copy">
            <h2>{{ title }}</h2>
            <p>{{ message }}</p>
          </div>
          <div class="dialog-actions">
            <button type="button" class="dialog-button" @click="emit('cancel')">
              取消
            </button>
            <button
              type="button"
              class="dialog-button is-primary"
              :class="{ 'is-danger': danger }"
              @click="emit('confirm')"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.dialog-root {
  position: fixed;
  inset: 0;
  z-index: 120;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(12, 33, 30, 0.34);
  backdrop-filter: blur(3px);
  -webkit-backdrop-filter: blur(3px);
}

.dialog-card {
  display: grid;
  width: min(420px, 100%);
  grid-template-columns: 40px minmax(0, 1fr);
  gap: 12px;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 18px;
  background: var(--surface);
  box-shadow: var(--shadow-lg);
}

.dialog-icon {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 12px;
  background: var(--amber-soft);
  color: var(--amber);
}

.dialog-icon.is-danger {
  background: var(--danger-soft);
  color: var(--danger);
}

.dialog-copy h2 {
  margin: 1px 0 5px;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
}

.dialog-copy p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 12px;
  line-height: 1.7;
}

.dialog-actions {
  display: flex;
  grid-column: 1 / -1;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 6px;
}

.dialog-button {
  height: 34px;
  padding: 0 15px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 650;
  transition:
    background 150ms ease,
    border-color 150ms ease,
    color 150ms ease;
}

.dialog-button:hover {
  border-color: var(--border-strong);
  background: var(--surface-soft);
  color: var(--text);
}

.dialog-button.is-primary {
  border-color: transparent;
  background: linear-gradient(135deg, #17ae99, #0c8b7b);
  color: #fff;
}

.dialog-button.is-primary:hover {
  background: linear-gradient(135deg, #14a28f, #0a7f70);
}

.dialog-button.is-primary.is-danger {
  border-color: transparent;
  background: var(--danger);
  color: #fff;
}

.dialog-button.is-primary.is-danger:hover {
  background: #c94646;
}

.dialog-enter-active,
.dialog-leave-active {
  transition: opacity 170ms ease;
}

.dialog-enter-active .dialog-card,
.dialog-leave-active .dialog-card {
  transition: transform 170ms ease;
}

.dialog-enter-from,
.dialog-leave-to {
  opacity: 0;
}

.dialog-enter-from .dialog-card,
.dialog-leave-to .dialog-card {
  transform: translateY(8px) scale(0.98);
}
</style>
