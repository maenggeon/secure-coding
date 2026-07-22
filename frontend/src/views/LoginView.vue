<template>
  <div class="card" style="max-width: 420px; margin: 2rem auto">
    <h2>로그인</h2>
    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label>아이디</label>
        <input v-model="username" required />
      </div>
      <div class="form-group">
        <label>비밀번호</label>
        <input v-model="password" type="password" required />
      </div>
      <button class="btn btn-primary" style="width: 100%" :disabled="loading">
        {{ loading ? '로그인 중...' : '로그인' }}
      </button>
    </form>
    <p style="margin-top: 1rem; text-align: center">
      계정이 없으신가요? <router-link to="/signup">회원가입</router-link>
    </p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const data = await auth.login(username.value, password.value)
    if (data.success) {
      router.push('/')
    } else {
      error.value = data.message
    }
  } catch (e) {
    error.value = e.response?.data?.message || '로그인에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>
