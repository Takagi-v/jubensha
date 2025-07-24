<template>
  <div class="action-input-panel">
    <!-- Final Reveal Button -->
    <template v-if="isFinalRevealDone && gameStore.game_state.current_stage !== 'game_over'">
      <div class="final-reveal-container">
        <el-button @click="triggerGameOver" type="danger" size="large" round>
          查看最终结局
        </el-button>
      </div>
    </template>

    <!-- Voting UI -->
    <template v-else-if="gameStore.game_state.pendingAction === 'vote'">
      <div v-if="gameStore.is_my_turn" class="vote-container">
        <el-select v-model="selectedTrust" placeholder="请选择信任对象">
          <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-select v-model="selectedSuspect" placeholder="请选择怀疑对象">
          <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
        </el-select>
        <el-button type="primary" @click="submitVote" :disabled="!canSubmitVote">提交投票</el-button>
      </div>
      <div v-else class="waiting-text">等待其他玩家投票...</div>
    </template>

    <!-- Accusation UI -->
    <template v-else-if="gameStore.game_state.pendingAction === 'accuse'">
      <div v-if="gameStore.is_my_turn" class="vote-container">
         <el-select v-model="selectedAccused" placeholder="请选择你要指认的凶手">
           <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
         </el-select>
        <el-button type="primary" @click="submitAccusation" :disabled="!selectedAccused">提交指认</el-button>
      </div>
      <div v-else class="waiting-text">等待其他玩家指认...</div>
    </template>

    <!-- Default Input UI -->
    <template v-else>
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
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useGameStore } from '../store/gameStore.js'
import websocketService from '../services/websocketService.js'

const gameStore = useGameStore()
const inputText = ref('')
const isSending = ref(false)

// 投票相关
const selectedTrust = ref('')
const selectedSuspect = ref('')
const canSubmitVote = computed(() => selectedTrust.value && selectedSuspect.value && selectedTrust.value !== selectedSuspect.value)

// 指认相关
const selectedAccused = ref('')

// 候选人（排除自己）
const voteCandidates = computed(() => 
  gameStore.game_state.players.filter(p => p.id !== gameStore.my_player_id && p.type !== 'dm')
)

// --- Computed Properties ---

const isFinalRevealDone = computed(() => {
  // Check if there are at least two 'turn' messages from the DM at the end.
  // This is more robust than checking for specific keywords.
  const dmTurnMessages = gameStore.messages.filter(msg => 
    msg.from_id === 'dm' && msg.type === 'turn'
  );
  return dmTurnMessages.length >= 2;
});

// --- Methods ---

const triggerGameOver = () => {
  gameStore.setGameState({ current_stage: 'game_over' });
};

const sendAction = () => {
  if (!inputText.value.trim() || !gameStore.is_my_turn) return
  
  isSending.value = true

  // Determine action_type based on game stage
  let actionType = 'DIALOGUE'; // default action
  let payload = { text: inputText.value };

  const stage = gameStore.game_state.current_stage;
  if (stage === 'alibi' || stage.startsWith('discussion')) {
    actionType = 'submit_statement';
    payload = { statement: inputText.value };
  }
  // We can add more conditions here for other stages like voting or accusation if needed

  const action = {
    type: actionType, // Changed from action_type to type to match backend
    payload: payload
  }

  const success = websocketService.sendAction(action)

  if (success) {
    inputText.value = ''
  }

  isSending.value = false
}

const submitVote = () => {
  if (!canSubmitVote.value) return
  const action = {
    type: 'submit_vote',
    payload: { trust: selectedTrust.value, suspect: selectedSuspect.value }
  }
  websocketService.sendAction(action)
  // 重置
  selectedTrust.value = ''
  selectedSuspect.value = ''
}

const submitAccusation = () => {
  if (!selectedAccused.value) return
  const action = {
    type: 'submit_accusation',
    payload: { accused_id: selectedAccused.value }
  }
  websocketService.sendAction(action)
  selectedAccused.value = ''
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

.vote-container {
  display: flex;
  gap: 8px;
  align-items: center;
}

.waiting-text {
  text-align: center;
  color: #909399;
  font-size: 14px;
  width: 100%;
}
.final-reveal-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}
</style> 