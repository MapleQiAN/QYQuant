<template>
  <div v-if="open" class="help-shell">
    <div class="help-overlay" @click="$emit('close')" />
    <aside class="help-panel" role="dialog" aria-label="帮助中心">
      <header class="help-header">
        <div>
          <h2 class="help-title">帮助中心</h2>
          <p class="help-subtitle">随时查概念、看指标解释、补操作说明。</p>
        </div>
        <button class="help-close" type="button" aria-label="关闭帮助中心" @click="$emit('close')">
          ×
        </button>
      </header>

      <div class="help-toolbar">
        <input
          v-model.trim="search"
          class="help-search"
          type="search"
          placeholder="搜索问题或指标"
          data-test="help-search"
        />
        <div class="help-categories">
          <button
            v-for="category in helpCategories"
            :key="category.id"
            :class="['help-chip', { active: activeCategory === category.id }]"
            type="button"
            :data-test="`help-category-${category.id}`"
            @click="activeCategory = category.id"
          >
            {{ category.label }}
          </button>
        </div>
      </div>

      <div class="help-list">
        <article v-for="entry in filteredEntries" :key="entry.id" class="help-item">
          <button
            class="help-question"
            type="button"
            :aria-expanded="expandedId === entry.id"
            @click="expandedId = expandedId === entry.id ? '' : entry.id"
          >
            <span>{{ entry.question }}</span>
            <span>{{ expandedId === entry.id ? '−' : '+' }}</span>
          </button>
          <p v-if="expandedId === entry.id" class="help-answer">{{ entry.answer }}</p>
        </article>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { helpCategories, helpEntries, type HelpCategory } from '../../data/help-content'

defineEmits<{
  (event: 'close'): void
}>()

const props = defineProps<{
  open: boolean
}>()

const search = ref('')
const activeCategory = ref<'all' | HelpCategory>('all')
const expandedId = ref('')

const filteredEntries = computed(() => {
  const keyword = search.value.toLowerCase()
  return helpEntries.filter((entry) => {
    const matchCategory = activeCategory.value === 'all' || entry.category === activeCategory.value
    const matchKeyword = !keyword || `${entry.question} ${entry.answer}`.toLowerCase().includes(keyword)
    return matchCategory && matchKeyword
  })
})

watch(() => props.open, (next) => {
  if (!next) {
    search.value = ''
    activeCategory.value = 'all'
    expandedId.value = ''
  }
})
</script>

<style scoped>
.help-shell {
  position: fixed;
  inset: 0;
  z-index: 200;
}

.help-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
}

.help-panel {
  position: absolute;
  top: 0;
  right: 0;
  width: min(400px, 100vw);
  height: 100%;
  padding: 24px 20px;
  background: #fff;
  box-shadow: -16px 0 40px rgba(15, 23, 42, 0.12);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.help-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.help-title {
  margin: 0;
  color: var(--color-text-primary);
}

.help-subtitle {
  margin: 6px 0 0;
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.help-close {
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: #94a3b8;
  font-size: 28px;
  cursor: pointer;
}

.help-toolbar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.help-search {
  width: 100%;
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 10px 14px;
  background: #f8fafc;
}

.help-categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.help-chip {
  border: 1px solid var(--color-border);
  border-radius: 999px;
  padding: 8px 12px;
  background: #fff;
  color: var(--color-text-secondary);
  cursor: pointer;
}

.help-chip.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

.help-list {
  overflow: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.help-item {
  border: 1px solid var(--color-border-light);
  border-radius: 16px;
  background: var(--color-surface);
}

.help-question {
  width: 100%;
  padding: 14px 16px;
  border: none;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: space-between;
  text-align: left;
  color: var(--color-text-primary);
  font-weight: var(--font-weight-semibold);
  cursor: pointer;
}

.help-answer {
  margin: 0;
  padding: 0 16px 16px;
  color: var(--color-text-secondary);
  line-height: 1.6;
}
</style>
