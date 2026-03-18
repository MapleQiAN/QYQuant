<template>
  <span class="verified-badge" data-test="verified-badge">
    Verified
  </span>
</template>

<style scoped>
.verified-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  background: rgba(24, 144, 255, 0.1);
  color: #1890ff;
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  white-space: nowrap;
}
</style>
