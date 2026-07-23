<template>
  <nav class="navbar">
    <div class="container nav-inner">
      <router-link to="/" class="logo">🛒 Tiny Market</router-link>
      <div class="nav-links">
        <router-link to="/">상품</router-link>
        <template v-if="auth.isLoggedIn">
          <router-link to="/products/new">판매</router-link>
          <router-link to="/my/products">내 상품</router-link>
          <router-link to="/chat">채팅</router-link>
          <router-link to="/my/page">마이페이지</router-link>
          <router-link v-if="auth.isAdmin" to="/admin">관리자</router-link>
          <span class="balance" v-if="auth.user">{{ auth.user.balance?.toLocaleString() }}원</span>
          <button class="btn btn-outline" @click="handleLogout">로그아웃</button>
        </template>
        <template v-else>
          <router-link to="/login">로그인</router-link>
          <router-link to="/signup">회원가입</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function handleLogout() {
  await auth.logout()
  router.push('/')
}
</script>

<style scoped>
.navbar {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 1.5rem;
}

.nav-inner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
}

.logo {
  font-size: 1.3rem;
  font-weight: 700;
  color: #333;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.nav-links a {
  color: #555;
  font-weight: 500;
}

.nav-links a.router-link-active {
  color: #4a90d9;
}

.balance {
  font-weight: 700;
  color: #e74c3c;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .nav-inner {
    flex-direction: column;
    gap: 0.8rem;
  }
}
</style>
