<template>
  <div v-if="loading" class="card">로딩 중...</div>
  <div v-else-if="user" class="card">
    <h2>{{ user.nickname }}</h2>
    <p>@{{ user.username }}</p>
    <p>{{ user.bio || '소개글이 없습니다.' }}</p>

    <h3 style="margin-top: 1.5rem">등록 상품</h3>
    <div class="grid">
      <div
        v-for="p in user.products"
        :key="p.id"
        class="product-card"
        @click="$router.push(`/products/${p.id}`)"
      >
        <img :src="imageUrl(p.image_path)" :alt="p.name" />
        <div class="info">
          <h3>{{ p.name }}</h3>
          <p class="price">{{ p.price.toLocaleString() }}원</p>
        </div>
      </div>
    </div>

    <div v-if="auth.isLoggedIn && auth.user.id !== user.id" class="actions">
      <button class="btn btn-primary" @click="startChat">1:1 채팅</button>
      <button class="btn btn-danger" @click="showReport = true">신고</button>
    </div>

    <div v-if="showReport" class="card" style="margin-top: 1rem">
      <h3>사용자 신고</h3>
      <textarea v-model="reportReason" rows="4" placeholder="신고 사유 (10자 이상)"></textarea>
      <button class="btn btn-danger" @click="submitReport">신고하기</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const user = ref(null)
const loading = ref(true)
const showReport = ref(false)
const reportReason = ref('')

function imageUrl(path) {
  return path ? `/api/uploads/${path}` : 'https://via.placeholder.com/300x200?text=No+Image'
}

async function fetchUser() {
  const { data } = await api.get(`/users/${route.params.id}`)
  if (data.success) user.value = data.data
  loading.value = false
}

async function startChat() {
  const { data } = await api.post('/chat/rooms/direct', { target_user_id: user.value.id })
  if (data.success) router.push({ path: '/chat', query: { room: data.data.room_id } })
}

async function submitReport() {
  const { data } = await api.post('/reports', {
    target_type: 'USER',
    target_id: user.value.id,
    reason: reportReason.value,
  })
  alert(data.message)
  showReport.value = false
}

onMounted(fetchUser)
</script>

<style scoped>
.actions {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}

textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}
</style>
