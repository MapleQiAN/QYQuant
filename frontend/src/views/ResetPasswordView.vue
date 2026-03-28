<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { resetPassword } from '../api/auth'

const route = useRoute()
const router = useRouter()

const password = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')

const token = computed(() => String(route.query.token || ''))

async function handleSubmit() {
  if (!token.value) {
    error.value = '缺少重置令牌'
    return
  }
  if (password.value.length < 8) {
    error.value = '密码至少 8 位'
    return
  }

  loading.value = true
  error.value = ''
  success.value = ''
  try {
    const result = await resetPassword(token.value, password.value)
    success.value = result.message
    await router.replace('/login')
  } catch (e: any) {
    error.value = e.message || '重置失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="auth-view">
    <div class="auth-card">
      <h1>重置密码</h1>
      <input v-model="password" class="field-input" type="password" placeholder="请输入新密码" data-test="reset-password" @keyup.enter="handleSubmit" />
      <p v-if="error" class="error-msg">{{ error }}</p>
      <p v-if="success" class="success-msg">{{ success }}</p>
      <button class="submit-btn" type="button" data-test="reset-submit" :disabled="loading" @click="handleSubmit">
        {{ loading ? '提交中...' : '更新密码' }}
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
