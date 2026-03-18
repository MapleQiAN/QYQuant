<template>
  <label class="registration-disclaimer" data-test="registration-disclaimer">
    <span class="checkbox-wrap">
      <input
        :checked="modelValue"
        aria-required="true"
        class="checkbox-input"
        data-test="registration-disclaimer-checkbox"
        type="checkbox"
        @change="handleChange"
      />
    </span>
    <span class="copy">
      我已阅读并同意
      <a
        :href="serviceAgreementHref"
        class="copy-link"
        data-test="service-agreement-link"
      >
        《服务协议》
      </a>
      与
      <a
        :href="disclaimerHref"
        class="copy-link"
        data-test="disclaimer-link"
      >
        《免责声明》
      </a>
    </span>
  </label>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  modelValue: boolean
  serviceAgreementHref?: string
  disclaimerHref?: string
}>(), {
  serviceAgreementHref: '#',
  disclaimerHref: '#',
})

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
}>()

function handleChange(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.checked)
}
</script>

<style scoped>
.registration-disclaimer {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-sm);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.checkbox-wrap {
  width: 44px;
  min-width: 44px;
  height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.checkbox-input {
  width: 16px;
  height: 16px;
}

.checkbox-input:focus-visible {
  outline: 2px solid #e53935;
  outline-offset: 2px;
}

.copy {
  padding-top: 12px;
}

.copy-link {
  color: #3b82f6;
}
</style>
