<template>
  <div class="card" style="max-width: 600px; margin: 0 auto">
    <h2>상품 등록</h2>
    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label>상품명</label>
        <input v-model="form.name" required />
      </div>
      <div class="form-group">
        <label>가격 (원)</label>
        <input v-model.number="form.price" type="number" min="0" required />
      </div>
      <div class="form-group">
        <label>상품 설명</label>
        <textarea v-model="form.description" rows="5" required></textarea>
      </div>
      <div class="form-group">
        <label>상품 사진</label>
        <input type="file" accept="image/*" @change="onFileChange" />
      </div>
      <button class="btn btn-primary" :disabled="loading">
        {{ loading ? '등록 중...' : '등록하기' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const form = reactive({ name: '', price: 0, description: '' })
const imageFile = ref(null)
const error = ref('')
const loading = ref(false)

function onFileChange(e) {
  imageFile.value = e.target.files[0]
}

async function handleSubmit() {
  error.value = ''
  loading.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('price', form.price)
    fd.append('description', form.description)
    if (imageFile.value) fd.append('image', imageFile.value)

    const { data } = await api.post('/products', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    if (data.success) {
      router.push(`/products/${data.data.id}`)
    } else {
      error.value = data.message
    }
  } catch (e) {
    error.value = e.response?.data?.message || '등록에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>
