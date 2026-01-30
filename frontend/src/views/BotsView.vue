<template>
  <section class="view">
    <div class="container">
      <h1 class="view-title">{{ $t('pages.botsTitle') }}</h1>
      <p class="view-subtitle">{{ $t('pages.botsSubtitle') }}</p>
    </div>
  </section>
</template>

<style scoped>
.view {
  width: 100%;
}

.view-title {
  margin: 0 0 var(--spacing-sm);
  font-size: var(--font-size-xl);
  color: var(--color-text-primary);
}

.view-subtitle {
  margin: 0;
  color: var(--color-text-muted);
}
</style>
