<template>
  <div class="app-root">
    <!-- Main Game Interface -->
    <div v-if="gameStore.welcomeSequenceCompleted" class="game-container">
      <el-container class="main-layout">
        <!-- Left Panel: My Info -->
        <el-aside width="300px" class="panel left-panel">
          <MyInfoPanel />
        </el-aside>

        <!-- Center Panel: Main Content -->
        <el-container class="center-container">
          <!-- Header: Status Bar -->
          <el-header height="auto" class="panel header-panel">
            <StatusBar />
          </el-header>
          <!-- Main: Chat and Actions -->
          <el-main class="panel main-panel">
            <ChatPanel />
            <ActionInput />
          </el-main>
        </el-container>

        <!-- Right Panel: Public Info -->
        <el-aside width="300px" class="panel right-panel">
          <PublicInfoPanel />
        </el-aside>
      </el-container>
    </div>
    
    <!-- Welcome Sequence Overlay -->
    <WelcomeSequence v-else />
  </div>
</template>

<script setup>
import { onMounted, watch } from 'vue'
import StatusBar from './components/StatusBar.vue'
import MyInfoPanel from './components/MyInfoPanel.vue'
import PublicInfoPanel from './components/PublicInfoPanel.vue'
import ChatPanel from './components/ChatPanel.vue'
import ActionInput from './components/ActionInput.vue'
import WelcomeSequence from './components/WelcomeSequence.vue' // 导入新组件
import websocketService from './services/websocketService.js'
import { useGameStore } from './store/gameStore.js'

const gameStore = useGameStore()

// 监听欢迎流程是否完成，完成后再连接WebSocket
watch(() => gameStore.welcomeSequenceCompleted, (completed) => {
  if (completed) {
    // 组件挂载时自动连接 WebSocket
    websocketService.connect(gameStore.my_player_id)
  }
})

</script>

<style scoped>
.app-root {
  height: 100vh;
  width: 100vw;
}
.game-container {
  height: 100%;
  width: 100%;
  background-color: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 16px;
  box-sizing: border-box;
}

.main-layout {
  width: 100%;
  height: 100%;
  max-width: 1600px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  overflow: hidden;
}

.panel {
  background-color: #ffffff;
  border: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.left-panel {
  border-right: none;
}

.right-panel {
  border-left: none;
}

.center-container {
  flex-grow: 1;
}

.header-panel {
  border-bottom: 1px solid #e8e8e8;
  padding: 0;
}

.main-panel {
  padding: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}
</style> 