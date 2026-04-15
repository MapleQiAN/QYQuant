<script setup lang="ts">
import { onMounted, ref } from 'vue'
import NotificationItem from './NotificationItem.vue'
import ConfirmDialog from './ConfirmDialog.vue'
import { registerNotificationHandlers } from '../../lib/toast'
import type { ConfirmOptions, NotificationOptions } from '../../lib/toast'

export interface ActiveNotification extends NotificationOptions {
  id: string
}

const notifications = ref<ActiveNotification[]>([])
const confirmState = ref<(ConfirmOptions & { visible: boolean; resolve: (v: boolean) => void }) | null>(null)

let counter = 0

function addNotification(options: NotificationOptions): string {
  const id = `notif-${++counter}-${Date.now()}`
  notifications.value = [...notifications.value, { ...options, id }]
  return id
}

function removeNotification(id: string) {
  notifications.value = notifications.value.filter(n => n.id !== id)
}

function showConfirm(options: ConfirmOptions): Promise<boolean> {
  return new Promise(resolve => {
    confirmState.value = { ...options, visible: true, resolve }
  })
}

function handleConfirmResult(result: boolean) {
  if (confirmState.value) {
    confirmState.value.resolve(result)
    confirmState.value = null
  }
}

onMounted(() => {
  registerNotificationHandlers(addNotification, showConfirm)
})
</script>

<template>
  <!-- Notification stack — top-right -->
  <div class="notification-container">
    <TransitionGroup name="notif-list" tag="div" class="notification-stack">
      <NotificationItem
        v-for="notif in notifications"
        :key="notif.id"
        v-bind="notif"
        @close="removeNotification"
      />
    </TransitionGroup>
  </div>

  <!-- Confirm dialog — centered overlay -->
  <ConfirmDialog
    v-if="confirmState"
    v-bind="confirmState"
    @confirm="handleConfirmResult(true)"
    @cancel="handleConfirmResult(false)"
  />
</template>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  pointer-events: none;
}

.notification-stack {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.notif-list-enter-active {
  transition: all 280ms cubic-bezier(0.2, 0, 0, 1);
}

.notif-list-leave-active {
  transition: all 240ms cubic-bezier(0.4, 0, 1, 1);
}

.notif-list-enter-from {
  opacity: 0;
  transform: translateX(40px) scale(0.96);
}

.notif-list-leave-to {
  opacity: 0;
  transform: translateX(40px) scale(0.96);
}

.notif-list-move {
  transition: transform 280ms cubic-bezier(0.2, 0, 0, 1);
}
</style>
