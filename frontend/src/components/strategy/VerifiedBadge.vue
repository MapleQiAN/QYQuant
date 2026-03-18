<template>
  <span class="verified-badge" data-test="verified-badge">
    Platform verified backtest
  </span>
</template>

<style scoped>
.verified-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.01em;
  white-space: nowrap;
}
</style>
