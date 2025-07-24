<template>
  <transition name="fade">
    <div v-if="visible" class="game-over-overlay">
      <div class="content-box">
        <h1 class="title">游戏结束</h1>
        <div class="results-text" v-html="typedText"></div>
        <el-button @click="restartGame" type="primary" size="large" class="restart-button">返回首页</el-button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { useGameStore } from '../store/gameStore.js';

const gameStore = useGameStore();
const visible = ref(false);
const typedText = ref('');
const fullText = ref('');

const gameOverMessages = computed(() => 
  gameStore.messages.filter(m => m.type === 'system' && m.content.includes('游戏结束'))
);

watch(() => gameStore.game_state.current_stage, (newStage) => {
  if (newStage === 'game_over') {
    visible.value = true;
    // Combine all game over messages into one block
    fullText.value = gameOverMessages.value.map(m => m.content).join('<br><br>');
    startTyping();
  }
});

const startTyping = () => {
  let i = 0;
  typedText.value = '';
  const typingInterval = setInterval(() => {
    if (i < fullText.value.length) {
      typedText.value += fullText.value.charAt(i);
      i++;
    } else {
      clearInterval(typingInterval);
    }
  }, 50); // Adjust typing speed here
};

const restartGame = () => {
  // This could be a hard reload or a more graceful state reset
  window.location.reload();
};

onMounted(() => {
  // Check if the game is already over when the component mounts
  if (gameStore.game_state.current_stage === 'game_over') {
    visible.value = true;
    fullText.value = gameOverMessages.value.map(m => m.content).join('<br><br>');
    startTyping();
  }
})
</script>

<style scoped>
.fade-enter-active, .fade-leave-active {
  transition: opacity 1.5s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.game-over-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  color: #fff;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

.content-box {
  background-color: rgba(20, 20, 20, 0.9);
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  width: 80%;
  max-width: 800px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.title {
  font-size: 3em;
  margin-bottom: 20px;
  font-weight: 300;
  letter-spacing: 2px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 20px;
}

.results-text {
  font-size: 1.2em;
  line-height: 1.8;
  margin-bottom: 30px;
  white-space: pre-wrap;
  text-align: left;
  min-height: 200px; /* To prevent layout shift */
  font-family: 'Courier New', Courier, monospace;
}

.restart-button {
  margin-top: 20px;
}
</style> 