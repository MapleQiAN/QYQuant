<template>
  <div class="notification-panel">
    <div class="notification-panel__header">
      <h3>通知中心</h3>
      <span class="notification-panel__meta">{{ notificationStore.unreadCount }} 未读</span>
    </div>

    <div v-if="notificationStore.isLoading" class="notification-panel__state">
      加载中...
    </div>
    <div v-else-if="notificationStore.notifications.length === 0" class="notification-panel__state">
      暂无通知
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
          <span class="notification-panel__content">{{ notification.content || '无内容摘要' }}</span>
          <span class="notification-panel__time">{{ notification.created_at || '' }}</span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useNotificationStore } from '../stores/useNotificationStore'

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
  top: calc(100% + 10px);
  right: 0;
  width: 360px;
  max-width: min(360px, calc(100vw - 24px));
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(203, 213, 225, 0.95);
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

.notification-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.notification-panel__header h3 {
  margin: 0;
  font-size: 15px;
  color: var(--color-text-primary);
}

.notification-panel__meta,
.notification-panel__time,
.notification-panel__content,
.notification-panel__state {
  color: var(--color-text-muted);
  font-size: 12px;
}

.notification-panel__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.notification-panel__item {
  border-radius: 12px;
  background: rgba(248, 250, 252, 0.95);
}

.notification-panel__item--unread {
  background: rgba(238, 242, 255, 0.72);
}

.notification-panel__button {
  width: 100%;
  padding: 12px;
  border: 0;
  background: transparent;
  text-align: left;
  display: grid;
  gap: 6px;
  cursor: pointer;
}

.notification-panel__title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: space-between;
}

.notification-panel__title {
  font-size: 13px;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.notification-panel__dot {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 999px;
  background: #ef4444;
}

@media (max-width: 768px) {
  .notification-panel {
    right: -8px;
    width: calc(100vw - 32px);
  }
}
</style>
