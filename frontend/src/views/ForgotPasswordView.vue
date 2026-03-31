<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { forgotPassword } from '../api/auth'
import { toast } from '../lib/toast'

const { t } = useI18n()
const email = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

async function handleSubmit() {
  if (!email.value.trim()) {
    error.value = t('auth.emailRequired')
    toast.error(error.value)
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const result = await forgotPassword(email.value.trim().toLowerCase())
    success.value = result.message
    toast.success(result.message)
  } catch (e: any) {
    error.value = e.message || t('forgotPassword.sendFailed')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-view">
    <div class="auth-card">
      <h1>{{ t('forgotPassword.title') }}</h1>
      <input v-model="email" class="field-input" type="email" :placeholder="t('auth.emailPlaceholder')" data-test="forgot-email" @keyup.enter="handleSubmit" />
      <p v-if="error" class="error-msg">{{ error }}</p>
      <p v-if="success" class="success-msg">{{ success }}</p>
      <button class="submit-btn" type="button" data-test="forgot-submit" :disabled="loading" @click="handleSubmit">
        {{ loading ? t('forgotPassword.submitting') : t('forgotPassword.submitButton') }}
      </button>
    </div>
  </section>
</template>

<style scoped>
.auth-view { display:flex; min-height:100vh; align-items:center; justify-content:center; padding:24px; background:var(--color-background); }
.auth-card { width:100%; max-width:420px; padding:32px; background:var(--glass-background); border:1px solid var(--glass-border); border-radius:24px; display:flex; flex-direction:column; gap:12px; }
.field-input { height:44px; padding:0 14px; border:1px solid var(--color-border); border-radius:var(--radius-lg); background:var(--color-surface); }
.submit-btn { height:44px; border:none; border-radius:var(--radius-lg); color:#fff; background:linear-gradient(135deg, var(--color-primary), var(--color-primary-dark)); }
.error-msg { color:var(--color-danger); margin:0; }
.success-msg { color:var(--color-success, #2f855a); margin:0; }
</style>
