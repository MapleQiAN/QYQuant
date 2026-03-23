<script setup lang="ts">
import { computed } from 'vue'
import type { UserPublicProfile } from '../../types/User'

const props = withDefaults(defineProps<{
  profile: UserPublicProfile
  editable?: boolean
}>(), {
  editable: false
})

const joinedLabel = computed(() => {
  if (!props.profile.created_at) {
    return '注册时间未知'
  }

  const date = new Date(props.profile.created_at)
  if (Number.isNaN(date.getTime())) {
    return '注册时间未知'
  }

  return `注册于 ${date.getFullYear()}年${date.getMonth() + 1}月`
})

const initial = computed(() => props.profile.nickname?.slice(0, 1)?.toUpperCase() || 'Q')
</script>

<template>
  <article class="profile-card">
    <div class="profile-main">
      <img
        v-if="profile.avatar_url"
        :src="profile.avatar_url"
        :alt="profile.nickname"
        class="avatar"
      />
      <div v-else class="avatar fallback">{{ initial }}</div>

      <div class="content">
        <div class="headline">
          <h1 class="nickname">{{ profile.nickname }}</h1>
          <span v-if="profile.is_banned" class="badge">已封禁</span>
        </div>
        <p class="bio">{{ profile.bio || '这个用户还没有留下个人简介。' }}</p>
        <p class="meta">{{ joinedLabel }}</p>
      </div>
    </div>

    <RouterLink v-if="editable" class="edit-link" to="/settings">编辑资料</RouterLink>
  </article>
</template>

<style scoped>
.profile-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding: 24px;
  border-radius: 24px;
  background:
    radial-gradient(circle at top left, rgba(14, 165, 233, 0.16), transparent 28%),
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(247, 250, 252, 0.96));
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
}

.profile-main {
  display: flex;
  gap: 20px;
  align-items: center;
}

.avatar {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.avatar.fallback {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #0f766e, #0ea5e9);
  color: #fff;
  font-size: 32px;
  font-weight: 700;
}

.content {
  display: grid;
  gap: 10px;
}

.headline {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.nickname {
  margin: 0;
  font-size: clamp(28px, 4vw, 40px);
  color: var(--color-text-primary);
}

.badge {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(220, 38, 38, 0.12);
  color: #b91c1c;
  font-size: 12px;
  font-weight: 600;
}

.bio,
.meta {
  margin: 0;
}

.bio {
  max-width: 720px;
  color: var(--color-text-secondary);
  line-height: 1.7;
}

.meta {
  color: var(--color-text-muted);
  font-size: 14px;
}

.edit-link {
  flex-shrink: 0;
  padding: 10px 16px;
  border-radius: 999px;
  background: #0f172a;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
}

@media (max-width: 768px) {
  .profile-card,
  .profile-main {
    flex-direction: column;
    align-items: flex-start;
  }

  .avatar,
  .avatar.fallback {
    width: 72px;
    height: 72px;
    font-size: 28px;
  }
}
</style>
