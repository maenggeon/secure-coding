<template>
  <div v-if="loading" class="card">로딩 중...</div>
  <div v-else-if="product" class="card">
    <div class="detail">
      <img :src="imageUrl(product.image_path)" :alt="product.name" class="main-image" />
      <div class="info">
        <h1>{{ product.name }}</h1>
        <p class="price">{{ product.price.toLocaleString() }}원</p>
        <p class="desc">{{ product.description }}</p>
        <div class="seller">
          <h3>판매자</h3>
          <router-link :to="`/users/${product.seller?.id}`">
            {{ product.seller?.nickname }} (@{{ product.seller?.username }})
          </router-link>
        </div>
        <div class="actions" v-if="auth.isLoggedIn">
          <button class="btn btn-primary" @click="startChat" v-if="!isOwner">1:1 채팅</button>
          <button class="btn btn-danger" @click="showReport = true" v-if="!isOwner">신고</button>
        </div>
      </div>
    </div>

    <div v-if="showReport" class="report-form card">
      <h3>상품 신고</h3>
      <textarea v-model="reportReason" rows="4" placeholder="신고 사유 (10자 이상)"></textarea>
      <div style="margin-top: 0.5rem">
        <button class="btn btn-danger" @click="submitReport">신고하기</button>
        <button class="btn btn-secondary" @click="showReport = false">취소</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const product = ref(null)
const loading = ref(true)
const showReport = ref(false)
const reportReason = ref('')

const isOwner = computed(() => product.value?.seller?.id === auth.user?.id)

function imageUrl(path) {
  return path ? `/api/uploads/${path}` : 'https://via.placeholder.com/400x300?text=No+Image'
}

async function fetchProduct() {
  const { data } = await api.get(`/products/${route.params.id}`)
  if (data.success) product.value = data.data
  loading.value = false
}

async function startChat() {
  const { data } = await api.post('/chat/rooms/direct', {
    target_user_id: product.value.seller.id,
  })
  if (data.success) router.push({ path: '/chat', query: { room: data.data.room_id } })
}

async function submitReport() {
  const { data } = await api.post('/reports', {
    target_type: 'PRODUCT',
    target_id: product.value.id,
    reason: reportReason.value,
  })
  alert(data.message)
  showReport.value = false
}

onMounted(fetchProduct)
</script>

<style scoped>
.detail {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.main-image {
  width: 100%;
  border-radius: 10px;
  max-height: 400px;
  object-fit: cover;
}

.price {
  font-size: 1.5rem;
  color: #e74c3c;
  font-weight: 700;
  margin: 0.5rem 0;
}

.desc {
  margin: 1rem 0;
  white-space: pre-wrap;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.report-form textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

@media (max-width: 768px) {
  .detail {
    grid-template-columns: 1fr;
  }
}
</style>
