<template>
  <section class="user-management">
    <div class="container user-management__container">
      <header class="user-management__hero">
        <div>
          <p class="user-management__eyebrow">Admin Console</p>
          <h1>用户管理</h1>
          <p>查看用户账号状态，执行封禁或解封，并在同一页面内审阅审计日志。</p>
        </div>
        <RouterLink class="user-management__back" to="/admin">返回后台首页</RouterLink>
      </header>

      <div class="user-management__tabs">
        <button
          type="button"
          class="user-management__tab"
          :class="{ 'user-management__tab--active': activeTab === 'users' }"
          data-test="tab-users"
          @click="activeTab = 'users'"
        >
          用户列表
        </button>
        <button
          type="button"
          class="user-management__tab"
          :class="{ 'user-management__tab--active': activeTab === 'audit' }"
          data-test="tab-audit-logs"
          @click="activeTab = 'audit'"
        >
          审计日志
        </button>
      </div>

      <section v-if="activeTab === 'users'" class="user-management__panel">
        <div class="user-management__toolbar">
          <input
            v-model="userSearch"
            data-test="user-search-input"
            class="user-management__input"
            type="text"
            placeholder="按手机号或昵称搜索"
            @keyup.enter="submitUserSearch"
          />
          <button
            type="button"
            class="user-management__primary"
            data-test="user-search-submit"
            @click="submitUserSearch"
          >
            搜索
          </button>
        </div>

        <div v-if="adminStore.userListLoading" class="user-management__empty">
          正在加载用户列表...
        </div>

        <div v-else-if="!adminStore.users.length" class="user-management__empty">
          暂无符合条件的用户。
        </div>

        <div v-else class="user-table">
          <table>
            <thead>
              <tr>
                <th>昵称</th>
                <th>手机号</th>
                <th>注册时间</th>
                <th>套餐</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in adminStore.users" :key="user.userId">
                <td>{{ user.nickname || '-' }}</td>
                <td>{{ user.phone || '-' }}</td>
                <td>{{ formatDate(user.createdAt) }}</td>
                <td>{{ user.planLevel || '-' }}</td>
                <td>
                  <span :class="user.isBanned ? 'status-badge status-badge--danger' : 'status-badge'">
                    {{ user.isBanned ? '已封禁' : '正常' }}
                  </span>
                </td>
                <td>
                  <button
                    v-if="!user.isBanned"
                    type="button"
                    class="table-action table-action--danger"
                    :data-test="`open-ban-${user.userId}`"
                    :disabled="isUpdatingUser(user.userId)"
                    @click="openDialog('ban', user.userId)"
                  >
                    封禁
                  </button>
                  <button
                    v-else
                    type="button"
                    class="table-action"
                    :data-test="`open-unban-${user.userId}`"
                    :disabled="isUpdatingUser(user.userId)"
                    @click="openDialog('unban', user.userId)"
                  >
                    解封
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="user-management__pagination">
          <button type="button" :disabled="adminStore.usersMeta.page <= 1" @click="changeUserPage(-1)">
            上一页
          </button>
          <span>第 {{ adminStore.usersMeta.page }} 页 / 共 {{ totalPages(adminStore.usersMeta) }} 页</span>
          <button
            type="button"
            :disabled="adminStore.usersMeta.page >= totalPages(adminStore.usersMeta)"
            @click="changeUserPage(1)"
          >
            下一页
          </button>
        </div>
      </section>

      <section v-else class="user-management__panel">
        <div class="audit-filters">
          <input
            v-model="auditFilters.action"
            data-test="audit-action-input"
            class="user-management__input"
            type="text"
            placeholder="操作类型"
          />
          <input
            v-model="auditFilters.operatorId"
            data-test="audit-operator-input"
            class="user-management__input"
            type="text"
            placeholder="操作人 ID"
          />
          <input
            v-model="auditFilters.targetType"
            class="user-management__input"
            type="text"
            placeholder="目标类型"
          />
          <input v-model="auditFilters.dateFrom" class="user-management__input" type="date" />
          <input v-model="auditFilters.dateTo" class="user-management__input" type="date" />
          <button
            type="button"
            class="user-management__primary"
            data-test="apply-audit-filters"
            @click="applyAuditFilters"
          >
            应用筛选
          </button>
        </div>

        <div v-if="adminStore.auditLogsLoading" class="user-management__empty">
          正在加载审计日志...
        </div>

        <div v-else-if="!adminStore.auditLogs.length" class="user-management__empty">
          暂无审计日志。
        </div>

        <div v-else class="audit-table">
          <table>
            <thead>
              <tr>
                <th>时间</th>
                <th>操作人</th>
                <th>动作</th>
                <th>目标</th>
                <th>详情</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in adminStore.auditLogs" :key="item.id">
                <td>{{ formatDate(item.createdAt) }}</td>
                <td>{{ item.operatorNickname || item.operatorId || '-' }}</td>
                <td>{{ item.action }}</td>
                <td>{{ `${item.targetType}:${item.targetId}` }}</td>
                <td>
                  <pre>{{ formatDetails(item.details) }}</pre>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="user-management__pagination">
          <button type="button" :disabled="adminStore.auditLogsMeta.page <= 1" @click="changeAuditPage(-1)">
            上一页
          </button>
          <span>第 {{ adminStore.auditLogsMeta.page }} 页 / 共 {{ totalPages(adminStore.auditLogsMeta) }} 页</span>
          <button
            type="button"
            :disabled="adminStore.auditLogsMeta.page >= totalPages(adminStore.auditLogsMeta)"
            @click="changeAuditPage(1)"
          >
            下一页
          </button>
        </div>
      </section>
    </div>

    <div v-if="dialog.open && activeUser" class="user-dialog__backdrop">
      <div class="user-dialog" role="dialog" aria-modal="true">
        <div class="user-dialog__header">
          <div>
            <p class="user-dialog__eyebrow">Account Action</p>
            <h3>{{ dialog.mode === 'ban' ? '封禁用户' : '解封用户' }}</h3>
          </div>
          <button type="button" class="user-dialog__ghost" @click="closeDialog">取消</button>
        </div>

        <p class="user-dialog__summary">
          目标用户：<strong>{{ activeUser.nickname || activeUser.userId }}</strong>
        </p>

        <textarea
          v-if="dialog.mode === 'ban'"
          v-model="dialog.reason"
          data-test="ban-dialog-reason"
          class="user-dialog__textarea"
          rows="4"
          maxlength="500"
          placeholder="请填写封禁原因"
        />

        <div class="user-dialog__footer">
          <button type="button" class="user-dialog__ghost" @click="closeDialog">取消</button>
          <button
            type="button"
            class="user-dialog__danger"
            data-test="confirm-ban-action"
            :disabled="isUpdatingUser(activeUser.userId)"
            @click="confirmDialog"
          >
            {{ dialog.mode === 'ban' ? '确认封禁' : '确认解封' }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { toast } from '../../lib/toast'
import { useAdminStore } from '../../stores/useAdminStore'

const adminStore = useAdminStore()
const activeTab = ref<'users' | 'audit'>('users')
const userSearch = ref('')
const auditFilters = reactive({
  operatorId: '',
  action: '',
  targetType: '',
  dateFrom: '',
  dateTo: ''
})
const dialog = reactive({
  open: false,
  mode: 'ban' as 'ban' | 'unban',
  userId: '',
  reason: ''
})

const activeUser = computed(() => adminStore.users.find((item) => item.userId === dialog.userId) ?? null)

onMounted(() => {
  void adminStore.loadUsers({ page: 1, perPage: 20, search: '' })
  void adminStore.loadAuditLogs({ page: 1, perPage: 20 })
})

function submitUserSearch() {
  void adminStore.loadUsers({
    page: 1,
    perPage: adminStore.usersMeta.perPage || 20,
    search: userSearch.value.trim()
  })
}

function changeUserPage(offset: number) {
  const page = Math.max(1, adminStore.usersMeta.page + offset)
  void adminStore.loadUsers({
    page,
    perPage: adminStore.usersMeta.perPage || 20,
    search: userSearch.value.trim()
  })
}

function changeAuditPage(offset: number) {
  const page = Math.max(1, adminStore.auditLogsMeta.page + offset)
  void adminStore.loadAuditLogs({
    ...auditFilters,
    page,
    perPage: adminStore.auditLogsMeta.perPage || 20
  })
}

function applyAuditFilters() {
  void adminStore.loadAuditLogs({
    operatorId: auditFilters.operatorId.trim(),
    action: auditFilters.action.trim(),
    targetType: auditFilters.targetType.trim(),
    dateFrom: auditFilters.dateFrom,
    dateTo: auditFilters.dateTo,
    page: 1,
    perPage: adminStore.auditLogsMeta.perPage || 20
  })
}

function openDialog(mode: 'ban' | 'unban', userId: string) {
  dialog.open = true
  dialog.mode = mode
  dialog.userId = userId
  dialog.reason = ''
}

function closeDialog() {
  dialog.open = false
  dialog.mode = 'ban'
  dialog.userId = ''
  dialog.reason = ''
}

function isUpdatingUser(userId: string): boolean {
  return Boolean(adminStore.banningUsers?.[userId])
}

async function confirmDialog() {
  if (!activeUser.value) return

  try {
    if (dialog.mode === 'ban') {
      const reason = dialog.reason.trim()
      if (!reason) {
        toast.error('请填写封禁原因')
        return
      }
      await adminStore.banUser(activeUser.value.userId, reason)
      toast.success('用户已封禁')
    } else {
      await adminStore.unbanUser(activeUser.value.userId)
      toast.success('用户已解封')
    }
    closeDialog()
  } catch (error) {
    toast.error(getErrorMessage(error))
  }
}

function totalPages(meta: { total: number; perPage: number }): number {
  const perPage = meta.perPage || 20
  return Math.max(1, Math.ceil((meta.total || 0) / perPage))
}

function formatDate(iso: string | null): string {
  if (!iso) return '-'
  const value = new Date(iso)
  if (Number.isNaN(value.getTime())) return iso
  const pad = (input: number) => String(input).padStart(2, '0')
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())} ${pad(value.getHours())}:${pad(value.getMinutes())}`
}

function formatDetails(details: Record<string, unknown>): string {
  return JSON.stringify(details ?? {}, null, 2)
}

function getErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message
  }
  return '操作失败，请稍后重试'
}
</script>

<style scoped>
.user-management__container {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.user-management__hero {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-lg);
  align-items: flex-start;
  padding: var(--spacing-xl);
  border-radius: 28px;
  background:
    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 42%),
    linear-gradient(135deg, rgba(15, 23, 42, 0.96), rgba(30, 64, 175, 0.92));
  color: var(--color-text-inverse);
}

.user-management__hero h1,
.user-management__hero p {
  margin: 0;
}

.user-management__eyebrow,
.user-dialog__eyebrow {
  margin-bottom: var(--spacing-xs);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-size: var(--font-size-sm);
}

.user-management__eyebrow {
  color: rgba(191, 219, 254, 0.92);
}

.user-management__back,
.user-management__primary,
.user-management__tab,
.table-action,
.user-dialog__ghost,
.user-dialog__danger {
  min-height: 42px;
  padding: 0 18px;
  border-radius: 999px;
  border: none;
  font: inherit;
}

.user-management__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.12);
  color: var(--color-text-inverse);
  text-decoration: none;
}

.user-management__tabs {
  display: flex;
  gap: var(--spacing-sm);
}

.user-management__tab {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
  cursor: pointer;
}

.user-management__tab--active {
  background: var(--color-primary);
  color: var(--color-text-inverse);
}

.user-management__panel {
  padding: var(--spacing-lg);
  border-radius: 24px;
  border: 1px solid var(--color-border-light);
  background: var(--color-surface);
  box-shadow: var(--shadow-md);
}

.user-management__toolbar,
.audit-filters,
.user-management__pagination,
.user-dialog__header,
.user-dialog__footer {
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

.user-management__toolbar,
.audit-filters {
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
}

.user-management__input,
.user-dialog__textarea {
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--color-border);
  border-radius: 16px;
  font: inherit;
}

.user-management__primary,
.user-dialog__danger,
.table-action--danger {
  background: var(--color-primary);
  color: var(--color-text-inverse);
  cursor: pointer;
}

.table-action {
  background: var(--color-border-light);
  color: var(--color-text-primary);
  cursor: pointer;
}

.table-action:disabled,
.user-dialog__danger:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.user-table table,
.audit-table table {
  width: 100%;
  border-collapse: collapse;
}

.user-table th,
.user-table td,
.audit-table th,
.audit-table td {
  padding: 14px 12px;
  border-bottom: 1px solid var(--color-border-light);
  text-align: left;
  vertical-align: top;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.12);
  color: var(--color-success);
}

.status-badge--danger {
  background: rgba(239, 68, 68, 0.12);
  color: var(--color-danger);
}

.user-management__empty {
  padding: var(--spacing-xl);
  border-radius: 18px;
  background: var(--color-surface-hover);
  color: var(--color-text-secondary);
  text-align: center;
}

.user-management__pagination {
  justify-content: flex-end;
  margin-top: var(--spacing-md);
}

.user-dialog__backdrop {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: var(--color-overlay);
  z-index: 20;
}

.user-dialog {
  width: min(520px, 100%);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  border-radius: 24px;
  border: 1px solid var(--color-border-light);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-lg);
}

.user-dialog__summary,
.user-dialog h3,
.user-dialog__header p {
  margin: 0;
}

.audit-table pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.85rem;
}

@media (max-width: 960px) {
  .user-management__hero,
  .user-management__pagination,
  .user-dialog__header,
  .user-dialog__footer {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
