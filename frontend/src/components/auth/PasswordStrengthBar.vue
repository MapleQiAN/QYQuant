<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{ password: string }>()
const { t } = useI18n()

const rules = computed(() => {
  const p = props.password
  return {
    length8: p.length >= 8,
    length12: p.length >= 12,
    mixedCase: /[a-z]/.test(p) && /[A-Z]/.test(p),
    hasDigit: /\d/.test(p),
    hasSpecial: /[^a-zA-Z0-9]/.test(p),
  }
})

const score = computed(() => {
  const r = rules.value
  return (r.length8 ? 1 : 0) + (r.length12 ? 1 : 0) + (r.mixedCase ? 1 : 0) + (r.hasDigit ? 1 : 0) + (r.hasSpecial ? 1 : 0)
})

const level = computed<'none' | 'weak' | 'fair' | 'good' | 'strong'>(() => {
  if (!props.password) return 'none'
  if (score.value <= 1) return 'weak'
  if (score.value === 2) return 'fair'
  if (score.value <= 3) return 'good'
  return 'strong'
})

const colorMap: Record<string, string> = {
  weak: 'var(--color-danger)',
  fair: 'var(--color-warning)',
  good: 'var(--color-primary)',
  strong: 'var(--color-success)',
}

const labelMap: Record<string, string> = {
  weak: t('auth.strengthWeak'),
  fair: t('auth.strengthFair'),
  good: t('auth.strengthGood'),
  strong: t('auth.strengthStrong'),
}
</script>

<template>
  <div v-if="level !== 'none'" class="password-strength" :data-level="level">
    <div class="strength-bar-track">
      <div
        v-for="i in 4"
        :key="i"
        class="strength-bar-segment"
        :class="{ filled: score >= i }"
        :style="{ backgroundColor: score >= i ? colorMap[level] : 'var(--color-border-light)' }"
      />
    </div>
    <span class="strength-label" :style="{ color: colorMap[level] }">
      {{ labelMap[level] }}
    </span>
  </div>
</template>

<style scoped>
.password-strength {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: -4px;
}

.strength-bar-track {
  display: flex;
  gap: 3px;
  flex: 1;
}

.strength-bar-segment {
  height: 4px;
  flex: 1;
  border-radius: 2px;
  transition: background-color var(--transition-fast);
}

.strength-label {
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}
</style>
