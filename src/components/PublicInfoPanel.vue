<template>
  <div class="public-info-panel">
    <el-card shadow="never" class="info-card">
      <template #header>
        <div class="card-header">
          <el-icon><UserFilled /></el-icon>
          <span>所有玩家</span>
        </div>
      </template>
      <div class="player-list" v-if="gameStore.game_state?.players">
        <el-card 
          v-for="player in gameStore.game_state.players" 
          :key="player.id" 
          class="player-card"
          :class="{ 'is-online': player.online, 'is-ai': player.type === 'ai', 'is-current': player.id === gameStore.game_state.current_player_id }"
        >
          <div class="player-header">
            <el-avatar :size="40" :class="`avatar-${player.type}`">{{ player.public_info.character_name.charAt(0) }}</el-avatar>
            <div class="player-details">
              <span class="player-name">{{ player.name }}</span>
              <span class="character-name">{{ player.public_info.character_name }}</span>
            </div>
          </div>
          <el-divider />
          <div class="player-status">
            <el-tag :type="player.online ? 'success' : 'info'" size="small">{{ player.online ? '在线' : '离线' }}</el-tag>
            <el-tag type="warning" size="small">{{ player.public_info.status }}</el-tag>
          </div>
        </el-card>
      </div>
      <el-empty v-else description="暂无玩家信息"></el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { UserFilled } from '@element-plus/icons-vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
</script>

<style scoped>
.public-info-panel {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
}
.info-card {
  height: 100%;
  border: none;
  display: flex;
  flex-direction: column;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.player-list {
  overflow-y: auto;
  flex-grow: 1;
  padding-right: 8px;
}
.player-card {
  margin-bottom: 12px;
  transition: all 0.2s ease-in-out;
}
.player-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}
.player-card.is-ai {
  border-left: 4px solid #409EFF;
}
.player-card.is-current {
  border: 2px solid #67C23A;
  box-shadow: 0 0 8px rgba(103, 194, 58, 0.4);
}
.player-card:not(.is-online) {
  opacity: 0.6;
}
.player-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.avatar-human {
  background-color: #67C23A;
}
.avatar-ai {
  background-color: #E6A23C;
}
.player-details {
  display: flex;
  flex-direction: column;
}
.player-name {
  font-weight: 500;
}
.character-name {
  font-size: 12px;
  color: #909399;
}
.player-status {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
}
</style> 