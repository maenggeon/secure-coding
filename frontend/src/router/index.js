import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/HomeView.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue') },
  { path: '/signup', name: 'Signup', component: () => import('../views/SignupView.vue') },
  { path: '/products/:id', name: 'ProductDetail', component: () => import('../views/ProductDetailView.vue') },
  { path: '/products/new', name: 'ProductNew', component: () => import('../views/ProductFormView.vue'), meta: { auth: true } },
  { path: '/my/products', name: 'MyProducts', component: () => import('../views/MyProductsView.vue'), meta: { auth: true } },
  { path: '/my/page', name: 'MyPage', component: () => import('../views/MyPageView.vue'), meta: { auth: true } },
  { path: '/users/:id', name: 'UserProfile', component: () => import('../views/UserProfileView.vue') },
  { path: '/chat', name: 'Chat', component: () => import('../views/ChatView.vue'), meta: { auth: true } },
  { path: '/transfer', name: 'Transfer', component: () => import('../views/TransferView.vue'), meta: { auth: true } },
  { path: '/admin', name: 'Admin', component: () => import('../views/AdminView.vue'), meta: { auth: true, admin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isLoggedIn) {
    next('/login')
  } else if (to.meta.admin && !auth.isAdmin) {
    next('/')
  } else {
    next()
  }
})

export default router
