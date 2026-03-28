<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { sendCode, login } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const userStore = useUserStore()

const phone = ref('')
const code = ref('')
const nickname = ref('')
const step = ref<'phone' | 'code' | 'nickname'>('phone')
const loading = ref(false)
const error = ref('')
const countdown = ref(0)

let countdownTimer: ReturnType<typeof setInterval> | null = null

function startCountdown(seconds: number) {
  countdown.value = seconds
  countdownTimer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = null
    }
  }, 1000)
}

async function handleSendCode() {
  if (!phone.value.trim()) {
    error.value = '请输入手机号'
    return
  }

  loading.value = true
  error.value = ''
  try {
    await sendCode(phone.value.trim())
    step.value = 'code'
    startCountdown(60)
  } catch (e: any) {
    if (e.code === 'RATE_LIMITED') {
      const retryAfter = e.message?.match(/\d+/)?.[0] || 60
      startCountdown(Number(retryAfter))
      step.value = 'code'
    } else {
      error.value = e.message || '发送验证码失败'
    }
  } finally {
    loading.value = false
  }
}

async function handleLogin() {
  if (!code.value.trim()) {
    error.value = '请输入验证码'
    return
  }

  loading.value = true
  error.value = ''
  try {
    const result = await login(
      phone.value.trim(),
      code.value.trim(),
      step.value === 'nickname' ? nickname.value.trim() : undefined,
    )
    localStorage.setItem('qyquant-token', result.access_token)
    await userStore.refreshProfile()
    router.replace('/')
  } catch (e: any) {
    if (e.code === 'NICKNAME_REQUIRED') {
      step.value = 'nickname'
      error.value = ''
    } else {
      error.value = e.message || '登录失败'
    }
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
  if (countdown.value > 0) return
  handleSendCode()
}
</script>

<template>
  <section class="login-view">
    <div class="login-card">
      <div class="login-header">
        <h1>QY Quant</h1>
        <p class="subtitle">量化交易平台</p>
      </div>

      <!-- Step 1: Phone -->
      <div v-if="step === 'phone'" class="login-form">
        <label class="field-label">手机号</label>
        <input
          v-model="phone"
          type="tel"
          class="field-input"
          placeholder="请输入手机号"
          maxlength="11"
          @keyup.enter="handleSendCode"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" @click="handleSendCode">
          {{ loading ? '发送中...' : '获取验证码' }}
        </button>
      </div>

      <!-- Step 2: Code -->
      <div v-else-if="step === 'code'" class="login-form">
        <label class="field-label">验证码</label>
        <p class="phone-hint">已发送至 {{ phone }}</p>
        <input
          v-model="code"
          type="text"
          class="field-input"
          placeholder="请输入6位验证码"
          maxlength="6"
          inputmode="numeric"
          @keyup.enter="handleLogin"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" @click="handleLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <button
          class="resend-btn"
          type="button"
          :disabled="countdown > 0"
          @click="handleResendCode"
        >
          {{ countdown > 0 ? `${countdown}s 后重新发送` : '重新发送验证码' }}
        </button>
      </div>

      <!-- Step 3: Nickname (new user) -->
      <div v-else class="login-form">
        <label class="field-label">设置昵称</label>
        <p class="phone-hint">首次登录，请设置您的昵称</p>
        <input
          v-model="nickname"
          type="text"
          class="field-input"
          placeholder="请输入昵称"
          maxlength="20"
          @keyup.enter="handleNicknameSubmit"
        />
        <p v-if="error" class="error-msg">{{ error }}</p>
        <button class="submit-btn" :disabled="loading" type="button" @click="handleNicknameSubmit">
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
  max-width: 400px;
  padding: 40px 32px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(15, 23, 42, 0.06);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.subtitle {
  margin: 6px 0 0;
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
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

.phone-hint {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

.field-input {
  height: 44px;
  padding: 0 14px;
  font-size: 15px;
  color: var(--color-text-primary);
  background: rgba(248, 250, 252, 0.92);
  border: 1px solid rgba(203, 213, 225, 0.95);
  border-radius: 12px;
  outline: none;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast);
}

.field-input:focus {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(129, 140, 248, 0.72);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.field-input::placeholder {
  color: var(--color-text-muted);
}

.error-msg {
  margin: 0;
  font-size: 13px;
  color: #b91c1c;
}

.submit-btn {
  height: 44px;
  margin-top: 4px;
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  border: none;
  border-radius: 12px;
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
