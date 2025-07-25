<template>
  <div class="action-input-panel">
    <!-- Final Reveal Button -->
    <div v-if="isFinalRevealDone" class="final-reveal-container">
      <el-button @click="triggerGameOver" type="danger" size="large" round>
        查看最终结局
      </el-button>
    </div>

    <!-- Voting UI (now independent) -->
    <div v-if="shouldShowVoteUI" class="vote-container">
      <el-select v-model="selectedTrust" placeholder="请选择信任对象">
        <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-select v-model="selectedSuspect" placeholder="请选择怀疑对象">
        <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="submitVote" :disabled="!canSubmitVote">提交投票</el-button>
    </div>

    <!-- Accusation UI (now independent) -->
    <div v-if="shouldShowAccuseUI" class="vote-container">
      <el-select v-model="selectedAccused" placeholder="请选择你要指认的凶手">
        <el-option v-for="p in voteCandidates" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <el-button type="primary" @click="submitAccusation" :disabled="!selectedAccused">提交指认</el-button>
    </div>

    <!-- Default Input UI (always visible) -->
    <div v-if="shouldShowDefaultInput" class="input-container">
      <el-input
        v-model="inputText"
        :placeholder="inputPlaceholder"
        :disabled="isInputDisabled"
        size="large"
        clearable
        @keyup.enter="sendAction"
      />
      <el-button
        type="primary"
        size="large"
        @click="sendAction"
        :disabled="isInputDisabled || !inputText.trim()"
        :loading="isSending"
      >
        发送
      </el-button>
    </div>
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

// --- Computed Properties for UI Logic ---

// 是否应该显示投票界面
const shouldShowVoteUI = computed(() => {
    return gameStore.game_state.pendingAction === 'vote' && gameStore.is_my_turn;
});

// 是否应该显示指认界面
const shouldShowAccuseUI = computed(() => {
    return gameStore.game_state.pendingAction === 'accuse' && gameStore.is_my_turn;
});

// 是否应该显示常规输入框
const shouldShowDefaultInput = computed(() => {
    // 只有在不进行投票或指认时才显示常规输入
    return !shouldShowVoteUI.value && !shouldShowAccuseUI.value;
});

// 输入框是否应该被禁用
const isInputDisabled = computed(() => {
  // 关键改动：不再使用 isMyStatementTurn，而是使用更通用的 is_my_turn
  // 只要不是我的回合，输入框就应该被禁用
  return !gameStore.is_my_turn;
});

// 输入框的占位符文本
const inputPlaceholder = computed(() => {
  // 使用 is_my_turn 进行判断
  if (gameStore.is_my_turn) {
    return '请输入你的发言内容...';
  }
  // 保留 AI 或其他玩家行动时的提示
  if (gameStore.game_state.current_player_id && gameStore.game_state.players.find(p => p.id === gameStore.game_state.current_player_id)?.type !== 'human') {
    const currentPlayer = gameStore.game_state.players.find(p => p.id === gameStore.game_state.current_player_id);
    return `等待 ${currentPlayer?.name || 'AI'} 行动中...`;
  }
  return '等待其他玩家行动...';
});


const isFinalRevealDone = computed(() => {
  // Check if there are at least two 'turn' messages from the DM at the end.
  // This is more robust than checking for specific keywords.
  const dmTurnMessages = gameStore.messages.filter(msg => 
    msg.from_id === 'dm' && msg.type === 'system'
  );
  return dmTurnMessages.length >= 2;
});

// --- Methods ---

const triggerGameOver = () => {
  gameStore.setGameState({ current_stage: 'game_over' });
};

const sendAction = () => {
  if (isInputDisabled.value || !inputText.value.trim()) return
  
  isSending.value = true

  // 这里的逻辑需要调整，以适应更通用的回合判断
  if (gameStore.isMyStatementTurn) {
    const action = {
        type: 'submit_statement',
        payload: { statement: inputText.value }
    };
    websocketService.sendAction(action.type, action.payload);
  } else {
    // 默认行为：如果不是陈述阶段但轮到我发言，就发送一个通用消息或执行其他默认操作
    // 在当前的游戏逻辑下，只有陈述阶段需要人类输入文本，所以这里可以暂时保留原来的逻辑
    // 但如果未来有自由聊天，这里就需要一个更通用的消息类型
    console.warn("Attempted to send message, but it's not a statement turn. Action ignored.");
  }
  
  inputText.value = ''
  isSending.value = false
}

const submitVote = () => {
  if (!canSubmitVote.value) return
  const action = {
    type: 'submit_vote',
    payload: { trust: selectedTrust.value, suspect: selectedSuspect.value }
  }
  websocketService.sendAction(action.type, action.payload)
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
  websocketService.sendAction(action.type, action.payload)
  selectedAccused.value = ''
}
</script>

<style scoped>
.action-input-panel {
  padding: 16px;
  background-color: #fafafa;
  border-top: 1px solid #e8e8e8;
  flex-shrink: 0; /* 禁止收缩，确保输入框高度稳定 */
}

.input-container {
  display: flex;
  gap: 8px;
}

.vote-container {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px; /* Add some space if both are somehow visible */
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