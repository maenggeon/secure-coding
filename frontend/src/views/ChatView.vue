<template>
  <div>
    <h2>채팅</h2>
    <div class="chat-layout">
      <div class="tabs">
        <button :class="{ active: tab === 'global' }" @click="switchTab('global')">전체 채팅</button>
        <button :class="{ active: tab === 'direct' }" @click="switchTab('direct')">1:1 채팅</button>
      </div>

      <div v-if="tab === 'direct'" class="direct-rooms card">
        <p v-if="!directRooms.length" class="empty">아직 1:1 대화가 없습니다. 상품 페이지에서 판매자에게 채팅을 시작해 보세요.</p>
        <button
          v-for="room in directRooms"
          :key="room.room_id"
          class="room-button"
          :class="{ active: directRoomId === room.room_id }"
          @click="openDirectRoom(room.room_id)"
        >
          <img :src="imageUrl(room.product?.image_path)" alt="상품 이미지" class="room-image" />
          <strong>{{ room.other_user.nickname }}</strong>
        </button>
      </div>

      <div class="chat-box card">
        <div class="messages" ref="msgContainer">
          <div v-for="m in messages" :key="m.id" class="message">
            <strong>{{ m.sender_nickname }}</strong>
            <span>{{ m.content }}</span>
            <small>{{ formatTime(m.created_at) }}</small>
          </div>
        </div>
        <form @submit.prevent="sendMessage" class="input-area">
          <input v-model="newMsg" placeholder="메시지 입력..." />
          <button class="btn btn-primary">전송</button>
          <button v-if="activeDirectRoom" type="button" class="btn btn-secondary" @click="showTransfer = true">송금하기</button>
        </form>
      </div>

      <div v-if="showTransfer && activeDirectRoom" class="transfer-modal">
        <div class="transfer-card card">
          <h3>{{ activeDirectRoom.other_user.nickname }}님에게 송금</h3>
          <p>현재 잔액: {{ auth.user?.balance?.toLocaleString() }}원</p>
          <div v-if="transferError" class="alert alert-error">{{ transferError }}</div>
          <input v-model.number="transferAmount" type="number" min="1" placeholder="송금액" />
          <div class="transfer-actions">
            <button class="btn btn-primary" :disabled="transferLoading" @click="sendTransfer">
              {{ transferLoading ? '처리 중...' : '송금하기' }}
            </button>
            <button class="btn btn-secondary" :disabled="transferLoading" @click="showTransfer = false">취소</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { io } from 'socket.io-client'
import api from '../api'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const tab = ref('global')
const messages = ref([])
const newMsg = ref('')
const msgContainer = ref(null)
const directRoomId = ref(null)
const directRooms = ref([])
const showTransfer = ref(false)
const transferAmount = ref(null)
const transferError = ref('')
const transferLoading = ref(false)
let socket = null

const activeDirectRoom = computed(() =>
  directRooms.value.find((room) => room.room_id === directRoomId.value)
)

function formatTime(d) {
  return new Date(d).toLocaleTimeString('ko-KR')
}

async function loadGlobalMessages() {
  const { data } = await api.get('/chat/rooms/global/messages')
  if (data.success) messages.value = data.data
  scrollBottom()
}

async function loadDirectMessages(roomId) {
  directRoomId.value = roomId
  const { data } = await api.get(`/chat/rooms/${roomId}/messages`)
  if (data.success) messages.value = data.data
  scrollBottom()
}

function imageUrl(path) {
  return path ? `/api/uploads/${path}` : 'https://via.placeholder.com/96x96?text=No+Image'
}

function generateIdempotencyKey() {
  return crypto.randomUUID()
}

async function loadDirectRooms() {
  const { data } = await api.get('/chat/rooms/direct')
  if (data.success) directRooms.value = data.data
}

async function openDirectRoom(roomId) {
  tab.value = 'direct'
  messages.value = []
  await loadDirectMessages(roomId)
  if (socket) socket.emit('join_direct', { token: auth.token, room_id: roomId })
}

function scrollBottom() {
  nextTick(() => {
    if (msgContainer.value) msgContainer.value.scrollTop = msgContainer.value.scrollHeight
  })
}

function connectSocket() {
  socket = io('/', { transports: ['websocket'] })

  socket.on('connect', () => {
    if (tab.value === 'global') {
      socket.emit('join_global', { token: auth.token })
    } else if (directRoomId.value) {
      socket.emit('join_direct', { token: auth.token, room_id: directRoomId.value })
    }
  })

  socket.on('global_message', (msg) => {
    if (tab.value === 'global') {
      messages.value.push(msg)
      scrollBottom()
    }
  })

  socket.on('direct_message', (msg) => {
    if (tab.value === 'direct' && msg.room_id === directRoomId.value) {
      messages.value.push(msg)
      scrollBottom()
    }
  })
}

async function switchTab(t) {
  tab.value = t
  messages.value = []
  if (t === 'global') {
    await loadGlobalMessages()
    if (socket) socket.emit('join_global', { token: auth.token })
  } else {
    directRoomId.value = null
    await loadDirectRooms()
  }
}

async function sendMessage() {
  if (!newMsg.value.trim()) return
  const content = newMsg.value
  newMsg.value = ''

  if (tab.value === 'global') {
    await api.post('/chat/rooms/global/messages', { content })
  } else if (directRoomId.value) {
    await api.post(`/chat/rooms/${directRoomId.value}/messages`, { content })
  }
}

async function sendTransfer() {
  transferError.value = ''
  if (!transferAmount.value || transferAmount.value < 1) {
    transferError.value = '송금액을 1원 이상 입력해주세요.'
    return
  }
  if (!confirm(`${transferAmount.value.toLocaleString()}원을 ${activeDirectRoom.value.other_user.nickname}님에게 송금하시겠습니까?`)) return

  transferLoading.value = true
  try {
    const { data } = await api.post('/transactions', {
      receiver_id: activeDirectRoom.value.other_user.id,
      amount: transferAmount.value,
      idempotency_key: generateIdempotencyKey(),
    })
    if (!data.success) throw new Error(data.message)
    await auth.refreshProfile()
    transferAmount.value = null
    showTransfer.value = false
    alert(data.message)
  } catch (e) {
    transferError.value = e.response?.data?.message || e.message || '송금에 실패했습니다.'
  } finally {
    transferLoading.value = false
  }
}

onMounted(async () => {
  connectSocket()
  if (route.query.room) {
    tab.value = 'direct'
    await loadDirectRooms()
    await loadDirectMessages(route.query.room)
    if (socket) socket.emit('join_direct', { token: auth.token, room_id: route.query.room })
  } else {
    await loadGlobalMessages()
  }
})

onUnmounted(() => {
  if (socket) socket.disconnect()
})
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
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
  border-color: #4a90d9;
}

.chat-box {
  display: flex;
  flex-direction: column;
  height: 500px;
}

.direct-rooms {
  margin-bottom: 1rem;
  padding: 0.5rem;
}

.room-button {
  display: grid;
  width: 100%;
  grid-template-columns: 56px 1fr;
  align-items: center;
  gap: 0.7rem;
  padding: 0.7rem;
  text-align: left;
  border: 0;
  border-radius: 6px;
  background: transparent;
  cursor: pointer;
}

.room-button:hover,
.room-button.active {
  background: #eef6ff;
}

.room-image {
  width: 56px;
  height: 56px;
  border-radius: 6px;
  object-fit: cover;
}

.empty {
  color: #666;
  font-size: 0.9rem;
}

.transfer-modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.45);
  z-index: 10;
}

.transfer-card {
  width: min(100%, 400px);
}

.transfer-card input {
  width: 100%;
  padding: 0.65rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.transfer-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.message {
  margin-bottom: 0.8rem;
}

.message strong {
  margin-right: 0.5rem;
}

.message small {
  display: block;
  color: #888;
  font-size: 0.75rem;
}

.input-area {
  display: flex;
  gap: 0.5rem;
  padding: 0.8rem;
  border-top: 1px solid #eee;
}

.input-area input {
  flex: 1;
  padding: 0.6rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}
</style>
