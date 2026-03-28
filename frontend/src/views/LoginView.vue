<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, sendCode, type AuthIdentifier } from '../api/auth'
import { useUserStore } from '../stores/user'

type LoginMode = 'phone' | 'email'
type LoginStep = 'identifier' | 'code' | 'nickname'

const PHONE_RE = /^1[3-9]\d{9}$/
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/

const router = useRouter()
const userStore = useUserStore()

const mode = ref<LoginMode>('phone')
const phone = ref('')
const email = ref('')
const code = ref('')
const nickname = ref('')
const step = ref<LoginStep>('identifier')
const loading = ref(false)
const error = ref('')
const countdown = ref(0)

let countdownTimer: ReturnType<typeof setInterval> | null = null

const currentIdentifier = computed(() =>
  mode.value === 'phone' ? phone.value.trim() : email.value.trim().toLowerCase(),
)

const identifierLabel = computed(() => (mode.value === 'phone' ? '手机号' : '邮箱'))

function resetCountdown() {
  if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  countdown.value = 0
}

function startCountdown(seconds: number) {
  resetCountdown()
  countdown.value = seconds
  countdownTimer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) {
      resetCountdown()
    }
  }, 1000)
}

function switchMode(nextMode: LoginMode) {
  if (mode.value === nextMode) {
    return
  }
  mode.value = nextMode
  code.value = ''
  nickname.value = ''
  error.value = ''
  step.value = 'identifier'
  resetCountdown()
}

function buildIdentifierPayload(): AuthIdentifier | null {
  if (mode.value === 'phone') {
    if (!phone.value.trim()) {
      error.value = '请输入手机号'
      return null
    }
    if (!PHONE_RE.test(phone.value.trim())) {
      error.value = '请输入正确的手机号'
      return null
    }
    return { phone: phone.value.trim() }
  }

  const normalizedEmail = email.value.trim().toLowerCase()
  if (!normalizedEmail) {
    error.value = '请输入邮箱'
    return null
  }
  if (!EMAIL_RE.test(normalizedEmail)) {
    error.value = '请输入正确的邮箱地址'
    return null
  }
  return { email: normalizedEmail }
}

async function handleSendCode() {
  const identifier = buildIdentifierPayload()
  if (!identifier) {
    return
  }

  loading.value = true
  error.value = ''
  try {
    await sendCode(identifier)
    step.value = 'code'
    startCountdown(60)
  } catch (e: any) {
    if (e.code === 'RATE_LIMITED') {
      const retryAfter = Number(e.message?.match(/\d+/)?.[0] || 60)
      step.value = 'code'
      startCountdown(retryAfter)
      return
    }
    error.value = e.message || '发送验证码失败'
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  const identifier = buildIdentifierPayload()
  if (!identifier) {
    return
  }
  if (!code.value.trim()) {
    error.value = '请输入验证码'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = await login({
      ...identifier,
      code: code.value.trim(),
      ...(step.value === 'nickname' ? { nickname: nickname.value.trim() } : {}),
    })
    localStorage.setItem('qyquant-token', result.access_token)
    await userStore.refreshProfile()
    await router.replace('/')
  } catch (e: any) {
    if (e.code === 'NICKNAME_REQUIRED') {
      step.value = 'nickname'
      error.value = ''
      return
    }
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}

async function handleNicknameSubmit() {
  if (!nickname.value.trim()) {
    error.value = '请输入昵称'
    return
  }
  await handleLogin()
}

function handleResendCode() {
  if (countdown.value > 0) {
    return
  }
  void handleSendCode()
}

onBeforeUnmount(() => {
  resetCountdown()
})
</script>

<template>
  <section class="login-view">
    <div class="login-card">
      <div class="login-header">
        <h1>QY Quant</h1>
        <p class="subtitle">量化交易平台</p>
      </div>

      <div class="mode-switch" role="tablist" aria-label="登录方式">
        <button
          class="mode-btn"
          :class="{ active: mode === 'phone' }"
          type="button"
          data-test="mode-phone"
          @click="switchMode('phone')"
        >
          手机号
        </button>
        <button
          class="mode-btn"
          :class="{ active: mode === 'email' }"
          type="button"
          data-test="mode-email"
          @click="switchMode('email')"
        >
          邮箱
        </button>
      </div>

      <div v-if="step === 'identifier'" class="login-form">
        <label class="field-label">{{ identifierLabel }}</label>
        <input
          v-if="mode === 'phone'"
          v-model="phone"
          type="tel"
          class="field-input"
          placeholder="请输入手机号"
          maxlength="11"
          data-test="phone-input"
          @keyup.enter="handleSendCode"
        />
        <input
          v-else
          v-model="email"
          type="email"
          class="field-input"
          placeholder="请输入邮箱"
          autocomplete="email"
          data-test="email-input"
          @keyup.enter="handleSendCode"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" data-test="send-code" @click="handleSendCode">
          {{ loading ? '发送中...' : '获取验证码' }}
        </button>
      </div>

      <div v-else-if="step === 'code'" class="login-form">
        <label class="field-label">验证码</label>
        <p class="identifier-hint">验证码已发送至 {{ currentIdentifier }}</p>
        <input
          v-model="code"
          type="text"
          class="field-input"
          placeholder="请输入 6 位验证码"
          maxlength="6"
          inputmode="numeric"
          data-test="code-input"
          @keyup.enter="handleLogin"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" data-test="submit-login" @click="handleLogin">
          {{ loading ? '登录中...' : '登录 / 注册' }}
        </button>
        <button class="resend-btn" type="button" :disabled="countdown > 0" data-test="resend-code" @click="handleResendCode">
          {{ countdown > 0 ? `${countdown}s 后重新发送` : '重新发送验证码' }}
        </button>
      </div>

      <div v-else class="login-form">
        <label class="field-label">设置昵称</label>
        <p class="identifier-hint">首次使用 {{ identifierLabel }} 登录，请先设置昵称。</p>
        <input
          v-model="nickname"
          type="text"
          class="field-input"
          placeholder="请输入昵称"
          maxlength="20"
          data-test="nickname-input"
          @keyup.enter="handleNicknameSubmit"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button
          class="submit-btn"
          :disabled="loading"
          type="button"
          data-test="submit-nickname"
          @click="handleNicknameSubmit"
        >
          {{ loading ? '注册中...' : '完成注册' }}
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
  max-width: 420px;
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

.mode-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 20px;
  padding: 6px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
}

.mode-btn {
  height: 40px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
  transition:
    background var(--transition-fast),
    color var(--transition-fast);
}

.mode-btn.active {
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

.identifier-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
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
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.field-input:focus {
  background: var(--color-surface-elevated);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.field-input::placeholder {
  color: var(--color-text-muted);
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
  transition: opacity var(--transition-fast);
}

.submit-btn:hover:not(:disabled) {
  opacity: 0.9;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.resend-btn {
  padding: 8px;
  font-size: 13px;
  color: var(--color-text-muted);
  background: none;
  border: none;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.resend-btn:hover:not(:disabled) {
  color: var(--color-primary);
}

.resend-btn:disabled {
  cursor: not-allowed;
}
</style>
