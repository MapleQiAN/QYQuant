<template>
  <div class="app">
    <!-- Top Navigation -->
    <TopNav />

    <!-- Main Content -->
    <main class="main-content">
      <RouterView />
    </main>

    <!-- Footer -->
    <footer class="app-footer">
      <div class="container footer-content">
        <span class="copyright">漏 2026 QY Quant. All rights reserved.</span>
        <div class="footer-links">
          <a href="#">甯姪涓績</a>
          <a href="#">API 鏂囨。</a>
          <a href="#">闅愮鏀跨瓥</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import TopNav from './components/TopNav.vue'
</script>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-background);
}

.main-content {
  flex: 1;
  padding: var(--spacing-lg) 0;
}

/* Footer */
.app-footer {
  padding: var(--spacing-lg) 0;
  border-top: 1px solid var(--color-border-light);
  margin-top: auto;
}

.footer-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copyright {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.footer-links {
  display: flex;
  gap: var(--spacing-lg);
}

.footer-links a {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-links a:hover {
  color: var(--color-primary);
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    gap: var(--spacing-md);
    text-align: center;
  }
}
</style>
