<template>
  <div class="action-input-panel">
    <div class="input-container">
      <el-input
        v-model="inputText"
        :placeholder="gameStore.is_my_turn ? '请输入发言内容...' : '现在是其他玩家的回合'"
        :disabled="!gameStore.is_my_turn"
        size="large"
        clearable
        @keyup.enter="sendAction"
      />
      <el-button 
        type="primary" 
        size="large" 
        @click="sendAction" 
        :disabled="!gameStore.is_my_turn || !inputText.trim()"
        :loading="isSending"
      >
        发送
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useGameStore } from '../store/gameStore.js'
import websocketService from '../services/websocketService.js'

const gameStore = useGameStore()
const inputText = ref('')
const isSending = ref(false)

const sendAction = () => {
  if (!inputText.value.trim() || !gameStore.is_my_turn) return
  
  isSending.value = true

  const action = {
    action_type: 'DIALOGUE',
    payload: {
      text: inputText.value,
    }
  }

  const success = websocketService.sendAction(action)

  if (success) {
    inputText.value = ''
  }

  isSending.value = false
}
</script>

<style scoped>
.action-input-panel {
  padding: 16px;
  background-color: #fafafa;
  border-top: 1px solid #e8e8e8;
}

.input-container {
  display: flex;
  gap: 8px;
}
</style> 