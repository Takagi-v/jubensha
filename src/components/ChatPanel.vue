<template>
  <div class="chat-panel">
    <div class="messages-container" ref="messagesContainer">
      <div v-for="message in gameStore.messages" :key="message.id" class="message-wrapper" :class="messageClass(message)">
        <div v-if="message.type === 'system'" class="system-message">
          <span>{{ message.content }}</span>
        </div>
        <div v-else class="chat-bubble">
          <div class="message-header">{{ message.from_name }}</div>
          <div class="message-content">{{ message.content }}</div>
          <div class="message-timestamp">{{ formatTimestamp(message.timestamp) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
const messagesContainer = ref(null)

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    const container = messagesContainer.value
    if (container) {
      container.scrollTop = container.scrollHeight
    }
  })
}

watch(() => gameStore.messages, () => {
  scrollToBottom()
}, { deep: true, immediate: true })


// 根据消息来源决定样式
const messageClass = (message) => {
  if (message.type === 'system') {
    return 'is-system'
  }
  return message.from_id === gameStore.my_player_id ? 'is-me' : 'is-other'
}

// 格式化时间戳
const formatTimestamp = (date) => {
  return new Date(date).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.chat-panel {
  flex-grow: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.messages-container {
  flex-grow: 1;
  overflow-y: auto;
  padding-right: 10px; /* for scrollbar */
}

.message-wrapper {
  margin-bottom: 16px;
  display: flex;
}

.is-me { justify-content: flex-end; }
.is-other { justify-content: flex-start; }
.is-system { justify-content: center; }

.chat-bubble {
  max-width: 70%;
  padding: 10px 15px;
  border-radius: 12px;
  position: relative;
}

.is-me .chat-bubble {
  background-color: #409EFF;
  color: white;
  border-top-right-radius: 4px;
}

.is-other .chat-bubble {
  background-color: #f0f2f5;
  color: #303133;
  border-top-left-radius: 4px;
}

.message-header {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 6px;
  opacity: 0.8;
}

.message-content {
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-timestamp {
  font-size: 10px;
  margin-top: 8px;
  text-align: right;
  opacity: 0.7;
}

.system-message {
  background-color: #e9e9eb;
  color: #909399;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
}
</style> 