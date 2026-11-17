<script setup lang="ts">
import { computed, ref, watch } from "vue";
import {
  Activity,
  AlertCircle,
  Check,
  ChevronDown,
  ChevronUp,
  Circle,
  LoaderCircle,
} from "lucide-vue-next";

import type { StepState } from "../types/agent";

const props = withDefaults(
  defineProps<{
    steps: StepState[];
    status?: "streaming" | "done" | "error";
  }>(),
  {
    status: "streaming",
  },
);

const expanded = ref(props.status === "streaming");

watch(
  () => props.status,
  (status) => {
    if (status === "streaming" || status === "error") {
      expanded.value = true;
    } else if (status === "done") {
      expanded.value = false;
    }
  },
);

const phaseOrder = ["理解问题", "检索数据", "整理上下文", "生成并执行", "其他"];

const phaseMap: Record<string, string> = {
  加载会话记忆: "理解问题",
  抽取关键词: "理解问题",
  召回字段信息: "检索数据",
  召回指标信息: "检索数据",
  召回字段取值: "检索数据",
  合并召回信息: "检索数据",
  过滤表信息: "整理上下文",
  过滤指标信息: "整理上下文",
  添加额外上下文: "整理上下文",
  增加额外上下文: "整理上下文",
  生成SQL: "生成并执行",
  校验SQL: "生成并执行",
  校正SQL: "生成并执行",
  执行SQL: "生成并执行",
  生成分析结论: "生成并执行",
};

const phases = computed(() => {
  const groups = new Map<string, StepState[]>();
  for (const step of props.steps) {
    const phase = phaseMap[step.step] ?? "其他";
    const list = groups.get(phase) ?? [];
    list.push(step);
    groups.set(phase, list);
  }

  return phaseOrder
    .filter((phase) => groups.has(phase))
    .map((phase) => ({ name: phase, steps: groups.get(phase) ?? [] }));
});

const runningStep = computed(() =>
  [...props.steps].reverse().find((step) => step.status === "running"),
);

const doneCount = computed(
  () => props.steps.filter((step) => step.status === "success").length,
);

const total = computed(() => props.steps.length);

const progress = computed(() => {
  if (total.value === 0) return props.status === "streaming" ? 8 : 0;
  return Math.max(6, Math.round((doneCount.value / total.value) * 100));
});

const summaryText = computed(() => {
  if (runningStep.value) return runningStep.value.step;
  if (props.status === "error") return "分析已中断";
  if (props.status === "done") return `${doneCount.value}/${total.value} 步完成`;
  return "等待执行";
});

function stateLabel(status: StepState["status"]) {
  if (status === "running") return "进行中";
  if (status === "success") return "完成";
  return "失败";
}
</script>

<template>
  <section class="step-panel">
    <button
      type="button"
      class="step-head"
      :aria-expanded="expanded"
      @click="expanded = !expanded"
    >
      <span class="step-heading">
        <Activity :size="15" />
        分析过程
        <span v-if="status === 'streaming'" class="live-tag">
          <span class="live-dot" aria-hidden="true" />
          实时
        </span>
      </span>

      <span class="step-summary">
        <span class="summary-text" :class="{ 'is-running': Boolean(runningStep) }">
          <LoaderCircle
            v-if="runningStep"
            class="spin"
            :size="13"
            aria-hidden="true"
          />
          {{ summaryText }}
        </span>
        <span class="progress-track" aria-hidden="true">
          <span class="progress-fill" :style="{ width: `${progress}%` }" />
        </span>
        <component :is="expanded ? ChevronUp : ChevronDown" :size="15" />
      </span>
    </button>

    <div v-if="expanded" class="step-body">
      <div v-if="!steps.length" class="step-connecting">
        <LoaderCircle class="spin" :size="15" />
        正在连接分析引擎…
      </div>

      <div v-for="phase in phases" :key="phase.name" class="phase">
        <div class="phase-label">{{ phase.name }}</div>
        <div class="phase-steps">
          <div
            v-for="step in phase.steps"
            :key="step.step"
            class="step-row"
            :class="`is-${step.status}`"
          >
            <span class="step-icon" aria-hidden="true">
              <LoaderCircle
                v-if="step.status === 'running'"
                class="spin"
                :size="14"
              />
              <Check v-else-if="step.status === 'success'" :size="14" />
              <AlertCircle v-else-if="step.status === 'error'" :size="14" />
              <Circle v-else :size="14" />
            </span>
            <span class="step-name">{{ step.step }}</span>
            <span class="step-state">{{ stateLabel(step.status) }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.step-panel {
  margin-top: 14px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 13px;
  background: var(--surface-soft);
}

.step-head {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 12px;
  border: 0;
  background: transparent;
  cursor: pointer;
  text-align: left;
}

.step-heading {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 650;
  white-space: nowrap;
}

.step-heading svg {
  color: var(--brand);
}

.live-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 6px;
  border-radius: 999px;
  background: var(--amber-soft);
  color: #9a640d;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.live-dot {
  width: 4px;
  height: 4px;
  border-radius: 999px;
  background: var(--amber);
  animation: pulse-soft 1.2s ease-in-out infinite;
}

.step-summary {
  display: inline-flex;
  min-width: 0;
  align-items: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 11px;
}

.summary-text {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  overflow: hidden;
  max-width: 170px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-text.is-running {
  color: #a0690e;
  font-weight: 600;
}

.progress-track {
  display: block;
  width: 62px;
  height: 4px;
  overflow: hidden;
  border-radius: 999px;
  background: #dfeae7;
}

.progress-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #16b29d, #4d8df7);
  transition: width 320ms ease;
}

.step-body {
  padding: 0 12px 12px;
  animation: fade-slide 180ms ease both;
}

.step-connecting {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  border-radius: 10px;
  background: var(--surface);
  color: var(--text-muted);
  font-size: 12px;
}

.phase + .phase {
  margin-top: 12px;
}

.phase-label {
  margin-bottom: 5px;
  padding-left: 2px;
  color: var(--text-muted);
  font-size: 9px;
  font-weight: 750;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.phase-steps {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.step-row {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr) auto;
  align-items: center;
  gap: 6px;
  padding: 6px 8px;
  border: 1px solid transparent;
  border-radius: 9px;
  background: rgba(255, 255, 255, 0.62);
}

.step-row.is-running {
  border-color: rgba(217, 139, 22, 0.18);
  background: var(--amber-soft);
}

.step-row.is-error {
  border-color: rgba(217, 82, 82, 0.16);
  background: var(--danger-soft);
}

.step-icon {
  display: grid;
  width: 20px;
  height: 20px;
  place-items: center;
  border-radius: 999px;
  background: rgba(23, 50, 46, 0.045);
  color: var(--text-muted);
}

.step-row.is-success .step-icon {
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.step-row.is-running .step-icon {
  background: rgba(217, 139, 22, 0.14);
  color: var(--amber);
}

.step-row.is-error .step-icon {
  background: rgba(217, 82, 82, 0.12);
  color: var(--danger);
}

.step-name {
  overflow: hidden;
  color: var(--text-secondary);
  font-size: 11.5px;
  font-weight: 550;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.step-row.is-success .step-name {
  color: var(--text);
}

.step-state {
  color: var(--text-muted);
  font-size: 9.5px;
}

.step-row.is-running .step-state {
  color: #9a640d;
  font-weight: 650;
}

.step-row.is-error .step-state {
  color: var(--danger);
}

@keyframes fade-slide {
  from {
    opacity: 0;
    transform: translateY(-3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 640px) {
  .step-head {
    align-items: flex-start;
    flex-direction: column;
    gap: 6px;
  }

  .step-summary {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
