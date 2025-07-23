<template>
  <div class="welcome-overlay">
    <div class="sequence-container">
      <!-- Step 1: Character Selection -->
      <div v-if="step === 'selection'" class="step-container character-selection">
        <h1>选择你的角色</h1>
        <div class="character-card" @click="selectCharacter">
          <el-avatar :size="100" class="character-avatar">管</el-avatar>
          <h2>忠诚的管家</h2>
          <p>“这座庄园的秘密，我了如指掌。”</p>
          <el-button type="primary" size="large">确认选择</el-button>
        </div>
        <p class="tip">（当前 Demo 仅开放一个角色）</p>
      </div>

      <!-- Step 2: Story Animation -->
      <div v-if="step === 'story'" class="step-container story-narration">
        <div class="story-text" v-html="displayedStory"></div>
        <el-button v-if="storyCompleted" type="primary" @click="step = 'info'">继续...</el-button>
      </div>

      <!-- Step 3: Info Reveal -->
      <div v-if="step === 'info'" class="step-container info-reveal">
        <h1>你的任务档案</h1>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="角色">{{ gameStore.my_info.character.name }}</el-descriptions-item>
          <el-descriptions-item label="描述">{{ gameStore.my_info.character.description }}</el-descriptions-item>
          <el-descriptions-item label="背景故事">{{ gameStore.my_info.background }}</el-descriptions-item>
          <el-descriptions-item label="任务目标">
            <el-tag v-for="obj in gameStore.my_info.objectives" :key="obj" style="margin-right: 5px;">{{ obj }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="私有线索">
            <el-tag v-for="clue in gameStore.my_info.private_clues" :key="clue" type="warning" style="margin-right: 5px;">{{ clue }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-button type="success" size="large" @click="startGame" class="start-game-btn">进入游戏</el-button>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { useGameStore } from '../store/gameStore'

const gameStore = useGameStore()
const step = ref('selection') // 'selection', 'story', 'info'

const displayedStory = ref('')
const storyCompleted = ref(false)
let typewriterInterval = null

const fullStory = `
<p>夜色如墨，笼罩着这座孤立于山间的古老庄园。</p>
<p>昨晚，一场盛大的宴会在此举行，以庆祝主人 acquisitions a new antique. 但欢乐的背后，暗流涌动。</p>
<p>今晨，主人的尸体在书房被发现，死状离奇。恐慌迅速蔓延，每个人都成了嫌疑人。</p>
<p>作为庄园的管家，你服务家族已有二十载，见证了这里的辉煌与衰败。</p>
<p>你比任何人都清楚，那光鲜的地毯下，掩盖着多少秘密与谎言。</p>
<p>现在，你必须在真相与忠诚之间做出抉择...</p>
`

const selectCharacter = () => {
  step.value = 'story'
  startTypewriter()
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

const startGame = () => {
  gameStore.completeWelcomeSequence()
}

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
  background-color: rgba(0, 0, 0, 0.85);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  color: #fff;
  text-align: center;
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
  background-color: #409EFF;
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
  min-height: 300px;
  width: 100%;
}
.story-text >>> p {
  margin-bottom: 1.5em;
}
.info-reveal {
  background-color: #fff;
  color: #333;
  padding: 30px;
  border-radius: 8px;
}
.start-game-btn {
  margin-top: 30px;
}
</style> 