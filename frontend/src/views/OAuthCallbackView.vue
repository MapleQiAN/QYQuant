<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { completeOAuth } from '../api/auth'
import { useUserStore } from '../stores/user'
import { toast } from '../lib/toast'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const userStore = useUserStore()

const error = ref('')
const loading = ref(true)

async function finalizeLogin(accessToken: string) {
  localStorage.setItem('qyquant-token', accessToken)
  userStore.profileLoaded = true
  userStore.profileLoading = false
  void userStore.refreshProfile().catch(() => {
    // OAuth login already succeeded; keep navigation independent from profile refresh.
  })
}

onMounted(async () => {
  const oauthToken = typeof route.query.oauth_token === 'string' ? route.query.oauth_token : ''

  if (!oauthToken) {
    error.value = 'Missing OAuth token'
    loading.value = false
    return
  }

  try {
    const result = await completeOAuth(oauthToken)
    toast.success(t('auth.loginTab') === 'Login' ? 'Login successful' : '登录成功')
    await finalizeLogin(result.access_token)
    await router.replace('/')
    setTimeout(() => {
      if (router.currentRoute.value.name === 'oauth-callback' || window.location.pathname === '/auth/oauth/callback') {
        window.location.href = '/'
      }
    }, 100)
  } catch (e: any) {
    error.value = e.message || 'OAuth login failed'
    loading.value = false
  }
})
</script>

<template>
  <section class="oauth-callback-view">
    <div class="oauth-callback-card">
      <template v-if="loading">
        <div class="oauth-spinner" />
        <p class="oauth-status">Completing login...</p>
      </template>
      <template v-else>
        <p class="oauth-error">{{ error }}</p>
        <button class="oauth-retry-btn" @click="router.replace('/login')">
          Back to Login
        </button>
      </template>
    </div>
  </section>
</template>

<style scoped>
.oauth-callback-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--color-background);
}

.oauth-callback-card {
  text-align: center;
  padding: 48px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
}

.oauth-spinner {
  width: 32px;
  height: 32px;
  margin: 0 auto 16px;
  border: 3px solid var(--color-border-light);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.oauth-status {
  color: var(--color-text-muted);
  font-size: 14px;
}

.oauth-error {
  color: var(--color-danger);
  font-size: 14px;
  margin-bottom: 16px;
}

.oauth-retry-btn {
  padding: 8px 24px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  font-family: inherit;
}
</style>
