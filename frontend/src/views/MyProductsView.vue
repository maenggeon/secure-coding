<template>
  <div>
    <h2>내 상품 관리</h2>
    <div v-if="loading" class="card">로딩 중...</div>
    <div v-else-if="products.length === 0" class="card">등록한 상품이 없습니다.</div>
    <div v-else class="grid">
      <div v-for="p in products" :key="p.id" class="product-card">
        <img :src="imageUrl(p.image_path)" :alt="p.name" @click="$router.push(`/products/${p.id}`)" />
        <div class="info">
          <h3>{{ p.name }}</h3>
          <p class="price">{{ p.price.toLocaleString() }}원</p>
          <span class="status">{{ p.status }}</span>
          <div class="actions">
            <button class="btn btn-danger btn-sm" @click="deleteProduct(p.id)">삭제</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const products = ref([])
const loading = ref(true)

function imageUrl(path) {
  return path ? `/api/uploads/${path}` : 'https://via.placeholder.com/300x200?text=No+Image'
}

async function fetchProducts() {
  const { data } = await api.get('/users/me/products')
  if (data.success) products.value = data.data
  loading.value = false
}

async function deleteProduct(id) {
  if (!confirm('정말 삭제하시겠습니까?')) return
  await api.delete(`/products/${id}`)
  fetchProducts()
}

onMounted(fetchProducts)
</script>

<style scoped>
.status {
  font-size: 0.8rem;
  color: #888;
}

.actions {
  margin-top: 0.5rem;
}

.btn-sm {
  padding: 0.3rem 0.8rem;
  font-size: 0.85rem;
}
</style>
