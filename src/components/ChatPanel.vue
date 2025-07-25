<template>
  <div class="chat-panel">
    <div class="header">公共聊天区</div>
    <div class="chat-body" ref="chatBody">
      <div v-for="message in gameStore.messages" :key="message.timestamp" class="message-wrapper">
        <div v-if="message.type === 'system'" class="system-message-container">
          <span class="system-message-content">{{ message.content }}</span>
        </div>
        <div v-else class="message-container" :class="{ 'my-message': message.from_id === gameStore.my_player_id, 'other-message': message.from_id !== gameStore.my_player_id }">
          <div class="sender-info">{{ message.from_name }}</div>
          <div class="message-bubble">
            {{ message.content }}
          </div>
        </div>
      </div>
    </div>
    <!-- 新增：正在输入提示 -->
    <div class="typing-indicator">
        {{ typingDisplay }}
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
const chatBody = ref(null)

const typingDisplay = computed(() => {
    const names = Object.values(gameStore.typing_players);
    if (names.length === 0) return '';
    if (names.length === 1) return `${names[0]} 正在输入...`;
    return `${names.join(', ')} 正在输入...`;
})

watch(() => gameStore.messages.length, () => {
  scrollToBottom()
})

const scrollToBottom = () => {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight
    }
  })
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  flex-grow: 1; /* 占据所有剩余空间 */
  min-height: 0; /* 修复 flex 布局下的滚动问题 */
  background-color: #f5f7fa;
}
.header {
  padding: 16px;
  font-weight: 600;
  border-bottom: 1px solid #e8e8e8;
  background-color: #ffffff;
  flex-shrink: 0; /* 防止 header 收缩 */
}
.chat-body {
  flex-grow: 1;
  overflow-y: auto;
  padding: 16px;
}
.typing-indicator {
    padding: 0 16px 10px;
    color: #909399;
    font-style: italic;
    font-size: 14px;
    height: 24px; /* 固定高度防止抖动 */
    flex-shrink: 0;
}
.message-container {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
}
.my-message {
  align-items: flex-end;
}
.other-message {
  align-items: flex-start;
}
.message-bubble {
  padding: 10px 15px;
  border-radius: 18px;
  max-width: 75%;
  word-wrap: break-word; /* 确保长单词能换行 */
  position: relative;
}
.my-message .message-bubble {
  background-color: #409EFF;
  color: #fff;
  border-bottom-right-radius: 5px;
}
.other-message .message-bubble {
  background-color: #fff;
  color: #303133;
  border: 1px solid #e9e9eb;
  border-bottom-left-radius: 5px;
}
.sender-info {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}
.system-message-container {
  text-align: center;
  margin: 16px 0;
}
.system-message-content {
  display: inline-block;
  padding: 6px 12px;
  background-color: #e9e9eb;
  color: #909399;
  font-size: 12px;
  border-radius: 12px;
}
</style> 