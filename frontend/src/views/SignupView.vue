<template>
  <div class="card" style="max-width: 480px; margin: 2rem auto">
    <h2>회원가입</h2>
    <div v-if="error" class="alert alert-error">{{ error }}</div>
    <div v-if="success" class="alert alert-success">{{ success }}</div>
    <form @submit.prevent="handleSignup">
      <div class="form-group">
        <label>아이디</label>
        <input v-model="form.username" required @blur="checkUsername" />
        <small v-if="usernameChecked !== null" :style="{ color: usernameChecked ? 'green' : 'red' }">
          {{ usernameChecked ? '사용 가능' : '이미 사용 중' }}
        </small>
      </div>
      <div class="form-group">
        <label>비밀번호</label>
        <input v-model="form.password" type="password" required />
        <small>8~24자, 영문 대/소문자·숫자·특수문자 중 3종류 이상</small>
      </div>
      <div class="form-group">
        <label>이메일</label>
        <input v-model="form.email" type="email" required @blur="checkEmail" />
        <small v-if="emailChecked !== null" :style="{ color: emailChecked ? 'green' : 'red' }">
          {{ emailChecked ? '사용 가능' : '이미 사용 중' }}
        </small>
      </div>
      <div class="form-group">
        <label>전화번호</label>
        <input v-model="form.phone" placeholder="010-1234-5678" required />
      </div>
      <div class="form-group">
        <label>닉네임</label>
        <input v-model="form.nickname" />
      </div>
      <button class="btn btn-primary" style="width: 100%" :disabled="loading">
        {{ loading ? '가입 중...' : '회원가입' }}
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'

const router = useRouter()
const form = reactive({ username: '', password: '', email: '', phone: '', nickname: '' })
const error = ref('')
const success = ref('')
const loading = ref(false)
const usernameChecked = ref(null)
const emailChecked = ref(null)

async function checkUsername() {
  if (!form.username) return
  const { data } = await api.get('/auth/check-username', { params: { username: form.username } })
  usernameChecked.value = data.data?.available ?? false
}

async function checkEmail() {
  if (!form.email) return
  const { data } = await api.get('/auth/check-email', { params: { email: form.email } })
  emailChecked.value = data.data?.available ?? false
}

async function handleSignup() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    const { data } = await api.post('/auth/signup', form)
    if (data.success) {
      success.value = '회원가입 완료! 로그인 페이지로 이동합니다.'
      setTimeout(() => router.push('/login'), 1500)
    } else {
      error.value = data.message
    }
  } catch (e) {
    error.value = e.response?.data?.message || '회원가입에 실패했습니다.'
  } finally {
    loading.value = false
  }
}
</script>
