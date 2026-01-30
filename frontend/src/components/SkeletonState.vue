<template>
  <div class="skeleton-state" role="status" aria-busy="true">
    <div class="skeleton-line title"></div>
    <div v-for="line in lines" :key="line" class="skeleton-line"></div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ lines?: number }>(), {
  lines: 4
})
</script>

<style scoped>
.skeleton-state {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
}

.skeleton-line {
  height: 12px;
  border-radius: var(--radius-sm);
  background: linear-gradient(90deg, var(--color-border-light), var(--color-surface), var(--color-border-light));
  background-size: 200% 100%;
  animation: shimmer 1.4s ease infinite;
}

.skeleton-line.title {
  height: 16px;
  width: 40%;
}

@keyframes shimmer {
  0% {
    background-position: 200% 0;
  }
  100% {
    background-position: -200% 0;
  }
}
</style>
