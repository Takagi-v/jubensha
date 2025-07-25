<template>
  <div class="status-bar">
    <div class="status-item">
      <el-icon><Menu /></el-icon>
      <span>阶段: <strong>{{ gameStore.game_state.current_stage_label || gameStore.game_state.current_stage }}</strong></span>
    </div>
    <div class="status-item">
      <el-icon><User /></el-icon>
      <span>当前玩家: <strong>{{ (gameStore.current_player?.public_info?.character_name) || '无' }}</strong></span>
    </div>
    <!-- 已移除回合显示 -->
  </div>
</template>

<script setup>
import { Menu, User } from '@element-plus/icons-vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
</script>

<style scoped>
.status-bar {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 12px 20px;
  background-color: #fff;
  border-bottom: 1px solid #e8e8e8;
  height: 60px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
}
.status-item strong {
  color: #303133;
  font-weight: 600;
}
</style> 