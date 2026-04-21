<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { loginWithPassword, registerWithPassword, initiateOAuth } from '../api/auth'
import { toast } from '../lib/toast'
import { useUserStore } from '../stores/user'
import PasswordStrengthBar from '../components/auth/PasswordStrengthBar.vue'
import WechatIcon from '../components/auth/icons/WechatIcon.vue'
import GithubIcon from '../components/auth/icons/GithubIcon.vue'
import GoogleIcon from '../components/auth/icons/GoogleIcon.vue'
import logoUrl from '../logo.png'

type AuthIntent = 'login' | 'register'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const intent = ref<AuthIntent>('login')
const email = ref('')
const password = ref('')
const nickname = ref('')
const confirmPassword = ref('')
const termsAccepted = ref(false)
const loading = ref(false)
const error = ref('')

function switchIntent(nextIntent: AuthIntent) {
  if (intent.value === nextIntent) {
    return
  }
  intent.value = nextIntent
  nickname.value = ''
  confirmPassword.value = ''
  termsAccepted.value = false
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
  if (intent.value === 'register' && password.value !== confirmPassword.value) {
    error.value = t('auth.passwordMismatch')
    toast.error(error.value)
    return null
  }
  if (intent.value === 'register' && !termsAccepted.value) {
    error.value = t('auth.termsRequired')
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
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
  const requiresProfileBeforeRedirect = router.resolve(redirect).matched.some((record) => record.meta.requiresAdmin)

  if (requiresProfileBeforeRedirect) {
    try {
      await userStore.refreshProfile()
    } catch {
      // Keep the authenticated redirect path; the admin guard will handle authorization.
    }
    await router.replace(redirect)
    return
  }

  userStore.profileLoaded = true
  userStore.profileLoading = false
  await router.replace(redirect)
  setTimeout(() => {
    const stillOnLoginRoute = router.currentRoute.value.name === 'login'
    const stillOnLoginUrl = window.location.pathname === '/login'
    if ((stillOnLoginRoute || stillOnLoginUrl) && !redirect.startsWith('/login')) {
      window.location.href = redirect
    }
  }, 100)
  void userStore.refreshProfile().catch(() => {
    // Login already succeeded; route guards can retry profile loading after navigation.
  })
}

async function startOAuth(provider: string) {
  try {
    const result = await initiateOAuth(provider)
    window.location.href = result.authorization_url
  } catch (e: any) {
    error.value = e.message || 'OAuth initiation failed'
  }
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
    <!-- Left: Animated Financial Scene -->
    <div class="login-scene">
      <div class="scene-grid"></div>
      <div class="scene-orb scene-orb--blue"></div>
      <div class="scene-orb scene-orb--gold"></div>
      <div class="scene-orb scene-orb--mid"></div>
      <div class="scene-stream"></div>
      <div class="scene-stream scene-stream--low"></div>
      <div class="scene-sticks">
        <span v-for="i in 6" :key="i" :class="'stick stick--' + i"></span>
      </div>
      <div class="scene-brand">
        <img :src="logoUrl" alt="QYQuant" class="scene-logo" />
        <h1 class="scene-title">QYQuant</h1>
        <p class="scene-tagline">智能量化交易平台</p>
        <div class="scene-divider"></div>
        <p class="scene-features">策略回测 · 模拟交易 · 社区分享</p>
      </div>
    </div>

    <!-- Right: Login Form -->
    <div class="login-panel">
      <div class="login-card">
        <div class="login-header">
          <img :src="logoUrl" alt="QYQuant" class="login-logo" />
          <h1>QYQuant</h1>
          <p class="login-subtitle">{{ intent === 'login' ? '欢迎回来' : '创建账户' }}</p>
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
          <div class="oauth-section">
            <button type="button" class="oauth-btn" data-test="oauth-wechat" @click="startOAuth('wechat')">
              <WechatIcon />
              <span>{{ t('auth.oauthWechat') }}</span>
            </button>
            <button type="button" class="oauth-btn" data-test="oauth-github" @click="startOAuth('github')">
              <GithubIcon />
              <span>{{ t('auth.oauthGithub') }}</span>
            </button>
            <button type="button" class="oauth-btn" data-test="oauth-google" @click="startOAuth('google')">
              <GoogleIcon />
              <span>{{ t('auth.oauthGoogle') }}</span>
            </button>
          </div>

          <div class="oauth-separator">
            <span class="separator-line" />
            <span class="separator-text">{{ t('auth.oauthSeparator') }}</span>
            <span class="separator-line" />
          </div>

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
            <PasswordStrengthBar :password="password" />

            <label class="field-label">{{ t('auth.confirmPasswordLabel') }}</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="field-input"
              :placeholder="t('auth.confirmPasswordPlaceholder')"
              autocomplete="new-password"
              data-test="confirm-password-input"
              @keyup.enter="handleSubmit"
            />
          </template>

          <RouterLink v-if="intent === 'login'" to="/forgot-password" class="forgot-link" data-test="forgot-link">
            {{ t('auth.forgotPassword') }}
          </RouterLink>

          <p v-if="error" class="error-msg">{{ error }}</p>

          <label v-if="intent === 'register'" class="terms-row">
            <input v-model="termsAccepted" type="checkbox" class="terms-checkbox" data-test="terms-checkbox" />
            <span class="terms-text">
              {{ t('auth.termsPrefix') }}
              <a href="/terms" target="_blank" class="terms-link">{{ t('auth.termsLink') }}</a>
            </span>
          </label>

          <button class="submit-btn" :disabled="loading" type="button" data-test="submit-auth" @click="handleSubmit">
            {{ loading ? (intent === 'register' ? t('auth.registering') : t('auth.loggingIn')) : (intent === 'register' ? t('auth.registerButton') : t('auth.loginButton')) }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* ===== Layout ===== */
.login-view {
  display: flex;
  min-height: 100vh;
  overflow: hidden;
}

/* ===== Scene — Left Panel ===== */
.login-scene {
  position: relative;
  flex: 1.15;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #081424 0%, #0d2240 40%, #091a30 100%);
  overflow: hidden;
}

/* Grid overlay */
.scene-grid {
  position: absolute;
  inset: -72px;
  background-image:
    repeating-linear-gradient(
      90deg,
      rgba(25, 118, 210, 0.05) 0,
      rgba(25, 118, 210, 0.05) 1px,
      transparent 1px,
      transparent 72px
    ),
    repeating-linear-gradient(
      0deg,
      rgba(25, 118, 210, 0.05) 0,
      rgba(25, 118, 210, 0.05) 1px,
      transparent 1px,
      transparent 72px
    );
  animation: gridDrift 25s linear infinite;
}

@keyframes gridDrift {
  from { transform: translate(0, 0); }
  to   { transform: translate(72px, 72px); }
}

/* Glowing orbs */
.scene-orb {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.scene-orb--blue {
  width: 360px;
  height: 360px;
  top: -10%;
  left: -12%;
  background: radial-gradient(circle, rgba(25, 118, 210, 0.24) 0%, transparent 70%);
  filter: blur(60px);
  animation: orbDrift 10s ease-in-out infinite;
}

.scene-orb--gold {
  width: 240px;
  height: 240px;
  bottom: 6%;
  right: 2%;
  background: radial-gradient(circle, rgba(249, 168, 37, 0.18) 0%, transparent 70%);
  filter: blur(50px);
  animation: orbDrift 13s ease-in-out infinite reverse;
}

.scene-orb--mid {
  width: 300px;
  height: 300px;
  top: 42%;
  left: 42%;
  background: radial-gradient(circle, rgba(25, 118, 210, 0.14) 0%, transparent 70%);
  filter: blur(70px);
  animation: orbDrift 15s ease-in-out infinite;
  animation-delay: -5s;
}

@keyframes orbDrift {
  0%, 100% { transform: translate(0, 0); }
  33%      { transform: translate(18px, -22px); }
  66%      { transform: translate(-12px, 16px); }
}

/* Horizontal data-stream lines */
.scene-stream {
  position: absolute;
  width: 200%;
  height: 1px;
  top: 58%;
  left: 0;
  background: repeating-linear-gradient(
    90deg,
    transparent 0px,
    rgba(25, 118, 210, 0.14) 2px,
    transparent 4px,
    transparent 28px
  );
  animation: streamSlide 11s linear infinite;
}

.scene-stream--low {
  top: 72%;
  opacity: 0.5;
  animation-duration: 14s;
  animation-direction: reverse;
}

@keyframes streamSlide {
  from { transform: translateX(-50%); }
  to   { transform: translateX(0); }
}

/* Candlestick-style vertical sticks */
.scene-sticks {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.stick {
  position: absolute;
  width: 1px;
  background: linear-gradient(to bottom, transparent, rgba(25, 118, 210, 0.2), transparent);
  animation: stickPulse 5s ease-in-out infinite;
}

.stick::before,
.stick::after {
  content: '';
  position: absolute;
  left: -2px;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: rgba(25, 118, 210, 0.28);
}

.stick::before { top: -2px; }
.stick::after  { bottom: -2px; }

.stick--1 { left: 12%; height: 38%; top: 28%; animation-delay: 0s; }
.stick--2 { left: 24%; height: 52%; top: 22%; animation-delay: -0.8s; opacity: 0.55; }
.stick--3 { left: 38%; height: 30%; top: 38%; animation-delay: -1.6s; }
.stick--4 { left: 52%; height: 46%; top: 26%; animation-delay: -2.4s; opacity: 0.65; }
.stick--5 { left: 68%; height: 34%; top: 36%; animation-delay: -3.2s; }
.stick--6 { left: 82%; height: 42%; top: 30%; animation-delay: -4s; opacity: 0.45; }

@keyframes stickPulse {
  0%, 100% { opacity: 0.25; }
  50%      { opacity: 0.7; }
}

/* Brand content */
.scene-brand {
  position: relative;
  z-index: 2;
  text-align: center;
  color: #fff;
  animation: brandIn 0.8s var(--ease-out-expo) both;
}

.scene-logo {
  width: 68px;
  height: 68px;
  margin-bottom: 18px;
  filter: drop-shadow(0 0 28px rgba(25, 118, 210, 0.35));
}

.scene-title {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 0;
  background: linear-gradient(135deg, #ffffff 30%, #90caf9 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.scene-tagline {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 6px;
  letter-spacing: 0.1em;
  font-weight: 500;
}

.scene-divider {
  width: 40px;
  height: 2px;
  background: rgba(249, 168, 37, 0.4);
  margin: 22px auto 18px;
  border-radius: 1px;
}

.scene-features {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.28);
  letter-spacing: 0.06em;
}

@keyframes brandIn {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== Form Panel — Right ===== */
.login-panel {
  flex: 0.85;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
  background: var(--color-background);
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 36px;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  animation: cardIn 0.6s var(--ease-out-expo) both;
  animation-delay: 0.15s;
}

@keyframes cardIn {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 28px;
}

.login-logo {
  width: 48px;
  height: 48px;
  margin-bottom: 12px;
}

.login-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

.login-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--color-text-muted);
}

/* Intent Switch */
.intent-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  margin-bottom: 20px;
  padding: 4px;
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-full);
}

.intent-btn {
  height: 38px;
  border: none;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: color var(--transition-fast), background var(--transition-fast);
  font-family: inherit;
}

.intent-btn.active {
  background: var(--color-primary);
  color: #fff;
}

/* Form Fields */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field-label {
  font-size: var(--font-size-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.field-input {
  height: 44px;
  padding: 0 14px;
  font-size: 14px;
  color: var(--color-text-primary);
  background: var(--color-surface-elevated);
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
  font-family: inherit;
}

.field-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
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
  font-weight: 600;
  color: #fff;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: opacity var(--transition-fast), transform var(--transition-fast);
  font-family: inherit;
}

.submit-btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Terms checkbox */
.terms-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
}

.terms-checkbox {
  width: 16px;
  height: 16px;
  margin-top: 2px;
  accent-color: var(--color-primary);
  cursor: pointer;
  flex-shrink: 0;
}

.terms-text {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.4;
}

.terms-link {
  color: var(--color-primary);
  text-decoration: none;
}

/* ===== OAuth ===== */
.oauth-section {
  display: flex;
  gap: 8px;
}

.oauth-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  height: 40px;
  border: 2px solid var(--color-border-light);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color var(--transition-fast), background var(--transition-fast);
  font-family: inherit;
}

.oauth-btn:hover {
  border-color: var(--color-primary);
  background: var(--color-primary-bg);
}

.oauth-separator {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 4px 0;
}

.separator-line {
  flex: 1;
  height: 1px;
  background: var(--color-border-light);
}

.separator-text {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .login-view {
    flex-direction: column;
    background: linear-gradient(160deg, #081424 0%, #0d2240 50%, #091a30 100%);
  }

  .login-scene {
    display: none;
  }

  .login-panel {
    flex: 1;
    min-height: 100vh;
    background: transparent;
  }

  .login-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-color: rgba(255, 255, 255, 0.15);
    box-shadow: 0 8px 40px rgba(0, 0, 0, 0.22);
  }
}

@media (max-width: 480px) {
  .login-panel {
    padding: 16px;
  }

  .login-card {
    padding: 28px 20px;
  }
}
</style>
