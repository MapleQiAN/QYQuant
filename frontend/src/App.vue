<script setup>
import { onMounted, ref } from "vue";

const health = ref(null);
const hello = ref(null);
const error = ref("");

async function fetchJson(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}

onMounted(async () => {
  try {
    health.value = await fetchJson("/api/health");
    hello.value = await fetchJson("/api/hello");
  } catch (e) {
    error.value = e?.message ?? String(e);
  }
});
</script>

<template>
  <main style="max-width: 960px; margin: 40px auto; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial">
    <h1 style="margin: 0 0 12px">QY_Quant</h1>
    <p style="margin: 0 0 24px; color: #555">Vue 前端通过 Vite 代理访问 Flask API（/api）。</p>

    <section style="padding: 16px; border: 1px solid #e5e5e5; border-radius: 12px">
      <h2 style="margin: 0 0 12px; font-size: 16px">API 状态</h2>
      <div v-if="error" style="color: #b00020">请求失败：{{ error }}</div>
      <div v-else>
        <div><b>/api/health</b>：{{ health }}</div>
        <div style="margin-top: 8px"><b>/api/hello</b>：{{ hello }}</div>
      </div>
    </section>
  </main>
</template>

