<template>
  <div class="card" style="max-width: 500px; margin: 0 auto">
    <h2>송금</h2>
    <p>현재 잔액: <strong>{{ auth.user?.balance?.toLocaleString() }}원</strong></p>
    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>

    <form @submit.prevent="handleTransfer">
      <div class="form-group">
        <label>수신자 사용자 ID</label>
        <input v-model.number="receiverId" type="number" required />
      </div>
      <div class="form-group">
        <label>송금액 (원)</label>
        <input v-model.number="amount" type="number" min="1" required />
      </div>
      <div class="confirm-box" v-if="receiverId && amount">
        <p>⚠️ 확인: <strong>{{ amount?.toLocaleString() }}원</strong>을 사용자 #{{ receiverId }}에게 송금합니다.</p>
      </div>
      <button class="btn btn-primary" style="width: 100%" :disabled="loading">
        {{ loading ? '처리 중...' : '송금하기' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const receiverId = ref(null)
const amount = ref(null)
const error = ref('')
const success = ref('')
const loading = ref(false)

function generateIdempotencyKey() {
  return crypto.randomUUID()
}

async function handleTransfer() {
  error.value = ''
  success.value = ''

  if (!confirm(`${amount.value?.toLocaleString()}원을 사용자 #${receiverId.value}에게 송금하시겠습니까?`)) {
    return
  }

  loading.value = true
  try {
    const { data } = await api.post('/transactions', {
      receiver_id: receiverId.value,
      amount: amount.value,
      idempotency_key: generateIdempotencyKey(),
    })
    if (data.success) {
      success.value = data.message
      await auth.refreshProfile()
      receiverId.value = null
      amount.value = null
    } else {
      error.value = data.message
    }
  } catch (e) {
    error.value = e.response?.data?.message || '송금에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.confirm-box {
  background: #fff3cd;
  padding: 0.8rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  border: 1px solid #ffc107;
}
</style>
