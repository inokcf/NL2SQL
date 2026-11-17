<script setup lang="ts">
import { computed, ref } from "vue";
import { Check, Copy, Database, Download } from "lucide-vue-next";

import {
  copyText,
  formatCell,
  isNumericValue,
  normalizeRows,
} from "../lib/format";

const props = defineProps<{
  data: unknown;
}>();

const rows = computed(() => normalizeRows(props.data));
const copied = ref(false);

const columns = computed(() => {
  const keys = new Set<string>();
  for (const row of rows.value) {
    Object.keys(row).forEach((key) => keys.add(key));
  }
  return Array.from(keys);
});

async function copyJson() {
  await copyText(JSON.stringify(props.data, null, 2));
  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1400);
}

function csvCell(value: unknown) {
  const text =
    value === null || value === undefined
      ? ""
      : typeof value === "object"
        ? JSON.stringify(value)
        : String(value);
  return `"${text.replace(/"/g, '""')}"`;
}

function downloadCsv() {
  const header = columns.value.map((column) => csvCell(column)).join(",");
  const body = rows.value
    .map((row) => columns.value.map((column) => csvCell(row[column])).join(","))
    .join("\n");
  const blob = new Blob([`﻿${header}\n${body}`], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `问数结果-${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
</script>

<template>
  <section class="result-card">
    <header class="result-head">
      <div class="result-title">
        <span class="result-icon" aria-hidden="true">
          <Database :size="15" />
        </span>
        <span>查询结果</span>
        <span v-if="columns.length" class="row-badge">{{ rows.length }} 行</span>
      </div>
      <div v-if="columns.length" class="result-actions">
        <button type="button" class="mini-action" @click="copyJson">
          <Check v-if="copied" :size="13" />
          <Copy v-else :size="13" />
          {{ copied ? "已复制" : "复制 JSON" }}
        </button>
        <button type="button" class="mini-action" @click="downloadCsv">
          <Download :size="13" />
          下载 CSV
        </button>
      </div>
    </header>

    <div v-if="columns.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th
              v-for="column in columns"
              :key="column"
              scope="col"
              :class="{ numeric: rows.some((row) => isNumericValue(row[column])) }"
            >
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in rows" :key="rowIndex">
            <td
              v-for="column in columns"
              :key="column"
              :class="{ numeric: isNumericValue(row[column]) }"
            >
              {{ formatCell(row[column]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="result-empty">
      查询完成，暂无可展示的数据。
    </div>
  </section>
</template>

<style scoped>
.result-card {
  margin-top: 14px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--surface);
  box-shadow: var(--shadow-xs);
}

.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-soft);
}

.result-title {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--text);
  font-size: 12px;
  font-weight: 650;
}

.result-icon {
  display: grid;
  width: 25px;
  height: 25px;
  place-items: center;
  border-radius: 8px;
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.row-badge {
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--surface-muted);
  color: var(--text-muted);
  font-size: 10px;
  font-weight: 600;
}

.result-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mini-action {
  display: inline-flex;
  height: 28px;
  align-items: center;
  gap: 5px;
  padding: 0 9px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 10.5px;
  font-weight: 600;
  transition:
    border-color 150ms ease,
    color 150ms ease,
    background 150ms ease;
}

.mini-action:hover {
  border-color: rgba(16, 156, 137, 0.22);
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.table-wrap {
  max-height: 380px;
  overflow: auto;
}

table {
  width: 100%;
  min-width: 520px;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 12px;
  text-align: left;
}

thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  padding: 10px 14px;
  border-bottom: 1px solid var(--border);
  background: #f2f8f6;
  color: var(--text-secondary);
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

tbody td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(226, 236, 233, 0.62);
  color: var(--text);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:nth-child(even) {
  background: rgba(248, 251, 250, 0.72);
}

tbody tr:hover {
  background: var(--surface-tint);
}

th.numeric,
td.numeric {
  text-align: right;
}

.result-empty {
  padding: 24px 14px;
  color: var(--text-muted);
  font-size: 12px;
  text-align: center;
}

@media (max-width: 640px) {
  .result-head {
    align-items: flex-start;
    flex-direction: column;
  }

  .result-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
