<template>
  <div>
    <h2>관리자 페이지</h2>
    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" :class="{ active: activeTab === t.key }" @click="activeTab = t.key">
        {{ t.label }}
      </button>
    </div>

    <!-- Users -->
    <div v-if="activeTab === 'users'" class="card">
      <table class="table">
        <thead>
          <tr><th>ID</th><th>아이디</th><th>닉네임</th><th>상태</th><th>잔액</th><th>조치</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.nickname }}</td>
            <td>{{ u.status }}</td>
            <td>{{ u.balance?.toLocaleString() }}</td>
            <td>
              <select @change="changeUserStatus(u.id, $event.target.value)" :value="u.status">
                <option value="ACTIVE">ACTIVE</option>
                <option value="SUSPENDED">SUSPENDED</option>
                <option value="BLOCKED">BLOCKED</option>
                <option value="DELETED">DELETED</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Products -->
    <div v-if="activeTab === 'products'" class="card">
      <table class="table">
        <thead>
          <tr><th>ID</th><th>상품명</th><th>가격</th><th>상태</th><th>신고수</th><th>조치</th></tr>
        </thead>
        <tbody>
          <tr v-for="p in products" :key="p.id">
            <td>{{ p.id }}</td>
            <td>{{ p.name }}</td>
            <td>{{ p.price?.toLocaleString() }}</td>
            <td>{{ p.status }}</td>
            <td>{{ p.report_count || 0 }}</td>
            <td>
              <button class="btn btn-sm" @click="changeProductStatus(p.id, 'ACTIVE')">복구</button>
              <button class="btn btn-sm btn-danger" @click="changeProductStatus(p.id, 'BLOCKED')">차단</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Reports -->
    <div v-if="activeTab === 'reports'" class="card">
      <div v-for="r in reports" :key="r.id" class="report-item">
        <p><strong>#{{ r.id }}</strong> [{{ r.target_type }}] #{{ r.target_id }} - {{ r.status }}</p>
        <p>{{ r.reason }}</p>
        <p><small>{{ r.reporter_nickname }} · {{ r.created_at }}</small></p>
        <div v-if="r.status === 'PENDING'">
          <button class="btn btn-danger btn-sm" @click="processReport(r.id, 'APPROVE')">승인(차단)</button>
          <button class="btn btn-secondary btn-sm" @click="processReport(r.id, 'REJECT')">반려</button>
        </div>
      </div>
    </div>

    <!-- Logs -->
    <div v-if="activeTab === 'logs'" class="card">
      <table class="table">
        <thead>
          <tr><th>시간</th><th>사용자</th><th>액션</th><th>상세</th><th>IP</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in logs" :key="l.id">
            <td>{{ l.created_at }}</td>
            <td>{{ l.user_id || '-' }}</td>
            <td>{{ l.action }}</td>
            <td>{{ l.details }}</td>
            <td>{{ l.ip_address }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import api from '../api'

const tabs = [
  { key: 'users', label: '회원 관리' },
  { key: 'products', label: '상품 관리' },
  { key: 'reports', label: '신고 처리' },
  { key: 'logs', label: '감사 로그' },
]
const activeTab = ref('users')
const users = ref([])
const products = ref([])
const reports = ref([])
const logs = ref([])

async function loadTab() {
  if (activeTab.value === 'users') {
    const { data } = await api.get('/admin/users')
    if (data.success) users.value = data.data
  } else if (activeTab.value === 'products') {
    const { data } = await api.get('/admin/products')
    if (data.success) products.value = data.data
  } else if (activeTab.value === 'reports') {
    const { data } = await api.get('/admin/reports')
    if (data.success) reports.value = data.data
  } else if (activeTab.value === 'logs') {
    const { data } = await api.get('/admin/logs')
    if (data.success) logs.value = data.data
  }
}

async function changeUserStatus(id, status) {
  await api.patch(`/admin/users/${id}/status`, { status })
  loadTab()
}

async function changeProductStatus(id, status) {
  await api.patch(`/admin/products/${id}/status`, { status })
  loadTab()
}

async function processReport(id, action) {
  await api.patch(`/admin/reports/${id}`, { action })
  loadTab()
}

watch(activeTab, loadTab)
onMounted(loadTab)
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.tabs button {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
}

.tabs button.active {
  background: #4a90d9;
  color: #fff;
}

.table {
  width: 100%;
  border-collapse: collapse;
}

.table th, .table td {
  padding: 0.6rem;
  border-bottom: 1px solid #eee;
  text-align: left;
  font-size: 0.9rem;
}

.report-item {
  padding: 1rem 0;
  border-bottom: 1px solid #eee;
}

.btn-sm {
  padding: 0.3rem 0.6rem;
  font-size: 0.8rem;
  margin-right: 0.3rem;
}
</style>
