<template>
  <span class="verified-badge" data-test="verified-badge">
    {{ $t('marketplace.verifiedBadge') }}
  </span>
</template>

<style scoped>
.verified-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  background: var(--color-primary-bg);
  color: var(--color-primary);
  border: 2px solid var(--color-primary);
  border-radius: 999px;
  font-size: var(--font-size-xs);
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}
</style>
