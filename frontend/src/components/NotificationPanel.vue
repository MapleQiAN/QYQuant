<template>
  <div class="notification-panel">
    <div class="notification-panel__header">
      <h3>{{ t('notifications.title') }}</h3>
      <span class="notification-panel__meta">{{ t('notifications.unreadCount', { count: notificationStore.unreadCount }) }}</span>
    </div>

    <div v-if="notificationStore.isLoading" class="notification-panel__state">
      {{ t('common.loading') }}
    </div>
    <div v-else-if="notificationStore.notifications.length === 0" class="notification-panel__state">
      {{ t('notifications.empty') }}
    </div>
    <ul v-else class="notification-panel__list">
      <li
        v-for="notification in notificationStore.notifications"
        :key="notification.id"
        :class="['notification-panel__item', { 'notification-panel__item--unread': !notification.is_read }]"
      >
        <button class="notification-panel__button" type="button" @click="handleOpen(notification.id)">
          <span class="notification-panel__title-row">
            <span class="notification-panel__title">{{ notification.title }}</span>
            <span v-if="!notification.is_read" class="notification-panel__dot" />
          </span>
          <span class="notification-panel__content">{{ notification.content || t('notifications.noContent') }}</span>
          <span class="notification-panel__time">{{ notification.created_at || '' }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNotificationStore } from '../stores/useNotificationStore'

const { t } = useI18n()
const notificationStore = useNotificationStore()

onMounted(() => {
  void notificationStore.fetchNotifications(1)
})

function handleOpen(notificationId: string) {
  void notificationStore.markAsRead(notificationId)
}
</script>

<style scoped>
.notification-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 340px;
  max-width: min(340px, calc(100vw - 24px));
  padding: 12px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
  z-index: 200;
}

.notification-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.notification-panel__header h3 {
  margin: 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.notification-panel__meta,
.notification-panel__time,
.notification-panel__content,
.notification-panel__state {
  color: var(--color-text-muted);
  font-size: var(--font-size-xs);
}

.notification-panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 4px;
}

.notification-panel__item {
  border-radius: var(--radius-md);
  background: var(--color-surface-hover);
}

.notification-panel__item--unread {
  background: var(--color-primary-bg);
}

.notification-panel__button {
  width: 100%;
  padding: 10px;
  border: 0;
  background: transparent;
  text-align: left;
  display: grid;
  gap: 4px;
  cursor: pointer;
}

.notification-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.notification-panel__title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.notification-panel__dot {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: var(--radius-full);
  background: var(--color-danger);
}

@media (max-width: 768px) {
  .notification-panel {
    right: -8px;
    width: calc(100vw - 32px);
  }
}
</style>
