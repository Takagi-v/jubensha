<template>
  <div class="welcome-overlay">
    <div class="sequence-container">
      <!-- Step 0: Initial Choice -->
      <div v-if="step === 'welcome' && !isReconnecting" class="step-container initial-choice">
        <h1>欢迎来到东方之星号谋杀案</h1>
        <el-button type="primary" size="large" @click="startNewGame">开始新游戏</el-button>
        <el-button :disabled="!hasSavedGame" type="warning" size="large" style="margin-top: 20px;" @click="reconnectGame">重新连接</el-button>
        <p v-if="!hasSavedGame" class="tip">（当前没有可重连的游戏）</p>
      </div>

      <!-- Step 0: Reconnecting Indicator -->
      <div v-if="isReconnecting" class="step-container reconnecting-indicator">
        <h1>正在重新连接到游戏...</h1>
        <el-icon class="is-loading" :size="40"><Loading /></el-icon>
        <p v-if="reconnectFailed" class="error-message">
          重连失败，请刷新页面或联系游戏管理员。
        </p>
      </div>

      <!-- Step 1: Character Selection -->
      <div v-if="step === 'selection' && !isReconnecting" class="step-container character-selection">
        <h1>选择你的角色</h1>
        <div class="character-card" @click="selectCharacter">
          <el-avatar :size="100" src="/figure/洪船长.png" class="character-avatar"></el-avatar>
          <h2>船长: 洪子廉</h2>
          <p>“这艘船，连同它所有的秘密，都在我的掌控之中。”</p>
          <el-button type="primary" size="large">确认选择</el-button>
        </div>
        <p class="tip">（当前 Demo 仅开放一个角色）</p>
      </div>

      <!-- Step 2: Story Animation -->
      <div v-if="step === 'story' && !isReconnecting" class="step-container story-narration">
        <div class="story-text" v-html="displayedStory"></div>
        <div class="story-actions">
          <el-button v-if="!storyCompleted" type="info" plain @click="skipTypewriter">跳过动画</el-button>
          <el-button v-if="storyCompleted" type="primary" @click="step = 'info'">继续...</el-button>
        </div>
      </div>

      <!-- Step 3: Info Reveal -->
      <div v-if="step === 'info'" class="step-container info-reveal">
        <h1>你的角色档案：船长 洪子廉</h1>
        <el-tabs v-model="activeInfoTab" class="info-tabs">
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="角色简介">{{ gameStore.my_info.character.description }}</el-descriptions-item>
              <el-descriptions-item label="不在场证明">{{ gameStore.my_info.statement }}</el-descriptions-item>
            </el-descriptions>
          </el-tab-pane>

          <el-tab-pane label="秘密任务" name="secrets">
            <div class="secrets-panel">
              <el-alert v-for="secret in gameStore.my_info.secrets" :key="secret"
                :title="secret" type="warning" :closable="false" show-icon class="secret-item"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane label="人际关系" name="relations">
            <el-collapse accordion>
              <el-collapse-item v-for="rel in gameStore.my_info.relationships" :key="rel.name" :title="rel.name">
                <div>{{ rel.desc }}</div>
              </el-collapse-item>
            </el-collapse>
          </el-tab-pane>

          <el-tab-pane label="行动时间线" name="timeline">
            <el-timeline>
              <el-timeline-item v-for="item in gameStore.my_info.timeline" :key="item.time" :timestamp="item.time">
                {{ item.event }}
              </el-timeline-item>
            </el-timeline>
          </el-tab-pane>
          
          <el-tab-pane label="持有信息" name="other_info">
            <div class="other-info-panel">
              <el-alert v-for="info in gameStore.my_info.other_info" :key="info"
                :title="info" type="info" :closable="false" show-icon class="info-item"
              />
            </div>
          </el-tab-pane>

          <el-tab-pane label="游戏目标" name="objectives">
             <div class="rules-panel">
                <p v-for="rule in gameStore.my_info.rules" :key="rule">{{ rule }}</p>
             </div>
          </el-tab-pane>
        </el-tabs>
        <el-button type="success" size="large" @click="startGame" class="start-game-btn">我已了解，进入游戏</el-button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted, onMounted, watch } from 'vue'
import { useGameStore } from '../store/gameStore'
import { Loading } from '@element-plus/icons-vue' // 引入 Loading 图标
import websocketService from '../services/websocketService.js'

const gameStore = useGameStore()
const step = ref('welcome') // 'welcome', 'selection', 'story', 'info'
const activeInfoTab = ref('basic')
const isReconnecting = ref(false)
const reconnectFailed = ref(false)
const hasSavedGame = ref(sessionStorage.getItem('game_in_progress') === 'true')

const displayedStory = ref('')
const storyCompleted = ref(false)
let typewriterInterval = null

const fullStory = `
<p><strong>【东方之星号豪华游轮谋杀案】</strong></p>
<p>2015年5月13日，夜幕降临，海风微咸。</p>
<p>这是“东方之星”号，在中日韩航线的最后绝唱。香槟、晚宴、甲板上绚烂的烟花... 一切都预示着一场完美的告别。</p>
<p>然而，在这片虚假的繁华之下，罪恶的暗流早已汹涌。</p>
<p>晚8时许，大副刘奇的尸体在阴冷的仓库中被发现。致命的伤口，凝固的血迹，将这艘海上宫殿瞬间拖入恐惧的深渊。</p>
<p>船，仍在航行。而凶手，就隐藏在我们中间。</p>
<p>船上的五个人，与死者关系千丝万缕，每个人都有嫌疑：</p>
<div class="suspect-list">
  <p><strong>洪子廉</strong> (船长)</p>
  <p><strong>张文远</strong> (二副)</p>
  <p><strong>修仁杰</strong> (酒吧经理)</p>
  <p><strong>韩亦暮</strong> (乘务员)</p>
  <p><strong>林若彤</strong> (驻场歌手)</p>
</div>
<p>现在，你即将成为他们中的一员。你的选择，将决定这场海上审判的最终结局。</p>
`

const selectCharacter = () => {
  step.value = 'story'
  startTypewriter()
}

const startNewGame = () => {
  step.value = 'selection'
}

const attemptReconnect = () => {
  const unwatch = watch(() => gameStore.is_connected, (connected) => {
      if(connected) {
          gameStore.completeWelcomeSequence()
          unwatch()
      }
  });

  websocketService.connect(gameStore.my_player_id)

  setTimeout(() => {
      if (!gameStore.is_connected) {
          reconnectFailed.value = true
          unwatch()
      }
  }, 10000)
}

const reconnectGame = () => {
  if (!hasSavedGame.value) {
    reconnectFailed.value = true
    return
  }
  isReconnecting.value = true
  attemptReconnect()
}

const startTypewriter = () => {
  let i = 0
  displayedStory.value = ''
  storyCompleted.value = false
  
  typewriterInterval = setInterval(() => {
    if (i < fullStory.length) {
      displayedStory.value += fullStory.charAt(i)
      i++
    } else {
      clearInterval(typewriterInterval)
      storyCompleted.value = true
    }
  }, 50) // 打字速度
}

const skipTypewriter = () => {
  clearInterval(typewriterInterval)
  displayedStory.value = fullStory
  storyCompleted.value = true
}

const startGame = () => {
  // 首次进入游戏时，设置标记
  sessionStorage.setItem('game_in_progress', 'true')
  gameStore.completeWelcomeSequence()
}

onMounted(() => {
  // 仅更新本地状态，用户自行选择是否重连
  hasSavedGame.value = sessionStorage.getItem('game_in_progress') === 'true'
})

onUnmounted(() => {
  clearInterval(typewriterInterval)
})
</script>

<style scoped>
.welcome-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-image: url('/figure/背景图.png');
  background-size: cover;
  background-position: center;
  /* background-color: rgba(0, 0, 0, 0.85); */
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  color: #fff;
  text-align: center;
}
.reconnecting-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}
.error-message {
  color: #F56C6C;
  font-weight: bold;
}
.sequence-container {
  max-width: 800px;
  width: 90%;
}
.step-container {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.character-card {
  padding: 30px;
  border: 1px solid #444;
  border-radius: 8px;
  background-color: #2c2c2c;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
}
.character-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.5);
}
.character-avatar {
  /* background-color: #409EFF; */
  font-size: 40px;
  margin-bottom: 20px;
}
.tip {
  margin-top: 20px;
  color: #888;
}
.story-narration {
  font-family: 'Courier New', Courier, monospace;
}
.story-text {
  font-size: 1.2em;
  line-height: 2;
  text-align: left;
  white-space: pre-wrap;
  padding: 20px;
  border: 1px solid #555;
  background: #1a1a1a;
  max-height: 65vh; /* 限制最大高度 */
  overflow-y: auto; /* 超出高度时显示滚动条 */
  width: 100%;
  margin-bottom: 20px; /* 与下方按钮的间距 */
}

/* 美化滚动条样式 */
.story-text::-webkit-scrollbar {
  width: 8px;
}
.story-text::-webkit-scrollbar-track {
  background: #2c2c2c;
}
.story-text::-webkit-scrollbar-thumb {
  background-color: #555;
  border-radius: 4px;
}

.story-text >>> p {
  margin-bottom: 1.5em;
}
.story-text >>> .suspect-list {
  padding: 10px 0;
  text-align: center;
  font-size: 0.9em;
  color: #ccc;
}
.info-reveal {
  background-color: #fff;
  color: #333;
  padding: 30px;
  border-radius: 8px;
  width: 100%;
}
.info-tabs {
  width: 100%;
  margin-top: 20px;
}
.secrets-panel, .rules-panel, .other-info-panel {
  text-align: left;
  line-height: 1.8;
}
.secret-item, .info-item {
  margin-bottom: 10px;
}
.start-game-btn {
  margin-top: 30px;
}
.story-actions {
  margin-top: 20px;
  display: flex;
  gap: 15px;
}
</style> 