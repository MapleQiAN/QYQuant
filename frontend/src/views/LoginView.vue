<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { loginWithPassword, registerWithPassword } from '../api/auth'
import { toast } from '../lib/toast'
import { useUserStore } from '../stores/user'

type AuthIntent = 'login' | 'register'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const intent = ref<AuthIntent>('login')
const email = ref('')
const password = ref('')
const nickname = ref('')
const loading = ref(false)
const error = ref('')

function switchIntent(nextIntent: AuthIntent) {
  if (intent.value === nextIntent) {
    return
  }
  intent.value = nextIntent
  nickname.value = ''
  error.value = ''
}

function validate() {
  const normalizedEmail = email.value.trim().toLowerCase()
  if (!normalizedEmail) {
    error.value = t('auth.emailRequired')
    toast.error(error.value)
    return null
  }
  if (!password.value) {
    error.value = t('auth.passwordRequired')
    toast.error(error.value)
    return null
  }
  if (password.value.length < 8) {
    error.value = t('auth.passwordTooShort')
    toast.error(error.value)
    return null
  }
  if (intent.value === 'register' && !nickname.value.trim()) {
    error.value = t('auth.nicknameRequired')
    toast.error(error.value)
    return null
  }
  return {
    email: normalizedEmail,
    password: password.value,
    nickname: nickname.value.trim(),
  }
}

async function finalizeLogin(accessToken: string) {
  localStorage.setItem('qyquant-token', accessToken)
  await userStore.refreshProfile()
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  await router.replace(redirect)
}

async function handleSubmit() {
  const payload = validate()
  if (!payload) {
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = intent.value === 'register'
      ? await registerWithPassword(payload)
      : await loginWithPassword({ email: payload.email, password: payload.password })
    toast.success(intent.value === 'register' ? '注册成功' : '登录成功')
    await finalizeLogin(result.access_token)
  } catch (e: any) {
    error.value = e.message || (intent.value === 'register' ? t('auth.registerFailed') : t('auth.loginFailed'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="login-view">
    <div class="login-card">
      <div class="login-header">
        <h1>{{ t('auth.title') }}</h1>
        <!-- <p class="subtitle">{{ t('auth.subtitle') }}</p> -->
      </div>

      <div class="intent-switch">
        <button
          class="intent-btn"
          :class="{ active: intent === 'login' }"
          type="button"
          data-test="login-tab"
          @click="switchIntent('login')"
        >
          {{ t('auth.loginTab') }}
        </button>
        <button
          class="intent-btn"
          :class="{ active: intent === 'register' }"
          type="button"
          data-test="register-tab"
          @click="switchIntent('register')"
        >
          {{ t('auth.registerTab') }}
        </button>
      </div>

      <div class="login-form">
        <label class="field-label">{{ t('auth.emailLabel') }}</label>
        <input
          v-model="email"
          type="email"
          class="field-input"
          :placeholder="t('auth.emailPlaceholder')"
          autocomplete="email"
          data-test="email-input"
          @keyup.enter="handleSubmit"
        />

        <label class="field-label">{{ t('auth.passwordLabel') }}</label>
        <input
          v-model="password"
          type="password"
          class="field-input"
          :placeholder="t('auth.passwordPlaceholder')"
          autocomplete="current-password"
          data-test="password-input"
          @keyup.enter="handleSubmit"
        />

        <template v-if="intent === 'register'">
          <label class="field-label">{{ t('auth.nicknameLabel') }}</label>
          <input
            v-model="nickname"
            type="text"
            class="field-input"
            :placeholder="t('auth.nicknamePlaceholder')"
            maxlength="20"
            data-test="nickname-input"
            @keyup.enter="handleSubmit"
          />
        </template>

        <RouterLink v-if="intent === 'login'" to="/forgot-password" class="forgot-link" data-test="forgot-link">
          {{ t('auth.forgotPassword') }}
        </RouterLink>

        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" data-test="submit-auth" @click="handleSubmit">
          {{ loading ? (intent === 'register' ? t('auth.registering') : t('auth.loggingIn')) : (intent === 'register' ? t('auth.registerButton') : t('auth.loginButton')) }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.login-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background: var(--color-background);
}

.login-card {
  width: 100%;
  max-width: 440px;
  padding: 40px 32px;
  background: var(--glass-background);
  border: 1px solid var(--glass-border);
  border-radius: 24px;
  box-shadow: var(--shadow-lg);
}

.login-header {
  text-align: center;
  margin-bottom: 24px;
}

.login-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.subtitle {
  margin: 6px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
}

.intent-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 20px;
  padding: 6px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
}

.intent-btn {
  height: 40px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.intent-btn.active {
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  color: #fff;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.field-input {
  height: 44px;
  padding: 0 14px;
  font-size: 15px;
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  outline: none;
}

.forgot-link {
  font-size: 13px;
  color: var(--color-primary);
  text-decoration: none;
  align-self: flex-end;
}

.error-msg {
  margin: 0;
  font-size: 13px;
  color: var(--color-danger);
}

.submit-btn {
  height: 44px;
  margin-top: 4px;
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
