<template>
  <div style="max-width: 600px; margin: 0 auto">
    <h2>마이페이지</h2>
    <div v-if="msg" :class="['alert', msgType === 'error' ? 'alert-error' : 'alert-success']">{{ msg }}</div>

    <div class="card">
      <h3>프로필 수정</h3>
      <form @submit.prevent="updateProfile">
        <div class="form-group">
          <label>닉네임</label>
          <input v-model="profile.nickname" />
        </div>
        <div class="form-group">
          <label>소개글</label>
          <textarea v-model="profile.bio" rows="3"></textarea>
        </div>
        <button class="btn btn-primary">저장</button>
      </form>
    </div>

    <div class="card">
      <h3>비밀번호 변경</h3>
      <form @submit.prevent="changePassword">
        <div class="form-group">
          <label>현재 비밀번호</label>
          <input v-model="pw.current" type="password" />
        </div>
        <div class="form-group">
          <label>새 비밀번호</label>
          <input v-model="pw.new" type="password" />
        </div>
        <button class="btn btn-primary">변경</button>
      </form>
    </div>

    <div class="card">
      <h3>내 송금 내역</h3>
      <div v-if="transactions.length === 0">내역 없음</div>
      <ul v-else class="tx-list">
        <li v-for="t in transactions" :key="t.id">
          {{ t.sender_id === auth.user.id ? '→' : '←' }}
          {{ t.amount.toLocaleString() }}원
          ({{ t.sender_id === auth.user.id ? t.receiver_nickname : t.sender_nickname }})
          <small>{{ formatDate(t.created_at) }}</small>
        </li>
      </ul>
    </div>

    <div class="card">
      <h3>내 신고 내역</h3>
      <div v-if="reports.length === 0">내역 없음</div>
      <ul v-else>
        <li v-for="r in reports" :key="r.id">
          [{{ r.target_type }}] #{{ r.target_id }} - {{ r.status }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const profile = reactive({ nickname: '', bio: '' })
const pw = reactive({ current: '', new: '' })
const transactions = ref([])
const reports = ref([])
const msg = ref('')
const msgType = ref('success')

function formatDate(d) {
  return new Date(d).toLocaleString('ko-KR')
}

async function loadData() {
  await auth.refreshProfile()
  profile.nickname = auth.user.nickname
  profile.bio = auth.user.bio

  const [txRes, rpRes] = await Promise.all([
    api.get('/users/me/transactions'),
    api.get('/users/me/reports'),
  ])
  if (txRes.data.success) transactions.value = txRes.data.data
  if (rpRes.data.success) reports.value = rpRes.data.data
}

async function updateProfile() {
  const { data } = await api.patch('/users/me', profile)
  msg.value = data.message
  msgType.value = data.success ? 'success' : 'error'
  if (data.success) await auth.refreshProfile()
}

async function changePassword() {
  const { data } = await api.patch('/users/me/password', {
    current_password: pw.current,
    new_password: pw.new,
  })
  msg.value = data.message
  msgType.value = data.success ? 'success' : 'error'
  if (data.success) {
    pw.current = ''
    pw.new = ''
  }
}

onMounted(loadData)
</script>

<style scoped>
.tx-list {
  list-style: none;
}

.tx-list li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.tx-list small {
  color: #888;
  margin-left: 0.5rem;
}
</style>
