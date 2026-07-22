<template>
  <div>
    <h1>중고거래 마켓</h1>
    <div class="search-bar card">
      <input v-model="query" placeholder="상품명 검색..." @keyup.enter="search" />
      <button class="btn btn-primary" @click="search">검색</button>
    </div>

    <div v-if="loading" class="card">로딩 중...</div>
    <div v-else-if="products.length === 0" class="card">등록된 상품이 없습니다.</div>
    <div v-else class="grid">
      <div
        v-for="p in products"
        :key="p.id"
        class="product-card"
        @click="$router.push(`/products/${p.id}`)"
      >
        <img :src="imageUrl(p.image_path)" :alt="p.name" />
        <div class="info">
          <h3>{{ p.name }}</h3>
          <p class="price">{{ p.price.toLocaleString() }}원</p>
          <small>{{ p.seller_nickname }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const products = ref([])
const query = ref('')
const loading = ref(true)

function imageUrl(path) {
  return path ? `/api/uploads/${path}` : 'https://via.placeholder.com/300x200?text=No+Image'
}

async function fetchProducts() {
  loading.value = true
  try {
    const params = query.value ? { q: query.value } : {}
    const { data } = await api.get('/products', { params })
    if (data.success) products.value = data.data.items
  } finally {
    loading.value = false
  }
}

function search() {
  fetchProducts()
}

onMounted(fetchProducts)
</script>

<style scoped>
h1 {
  margin-bottom: 1rem;
}

.search-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.search-bar input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}
</style>
