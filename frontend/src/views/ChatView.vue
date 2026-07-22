<template>
  <div>
    <h2>채팅</h2>
    <div class="chat-layout">
      <div class="tabs">
        <button :class="{ active: tab === 'global' }" @click="switchTab('global')">전체 채팅</button>
        <button :class="{ active: tab === 'direct' }" @click="switchTab('direct')">1:1 채팅</button>
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
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
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
let socket = null

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

onMounted(async () => {
  connectSocket()
  if (route.query.room) {
    tab.value = 'direct'
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
