<template>
  <footer
    aria-label="免责声明"
    class="disclaimer-footer"
    data-test="disclaimer-footer"
    role="contentinfo"
  >
    <p class="disclaimer-text">{{ text }}</p>
  </footer>
</template>

<script setup lang="ts">
import { BACKTEST_FOOTER_DISCLAIMER } from '../../data/disclaimer-content'

withDefaults(defineProps<{
  text?: string
}>(), {
  text: BACKTEST_FOOTER_DISCLAIMER,
})
</script>

<style scoped>
.disclaimer-footer {
  margin-top: var(--spacing-md);
  padding-top: 12px;
  border-top: 1px solid #e5e5e5;
}

.disclaimer-text {
  margin: 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
  line-height: var(--line-height-normal);
  text-align: center;
  user-select: none;
}
</style>
