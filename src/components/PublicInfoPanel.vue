<template>
  <div class="public-info-panel">
    <div class="header">
      <el-icon><UserFilled /></el-icon>
      <span>所有玩家</span>
    </div>
    <div class="player-list-container">
      <el-card 
        v-for="player in gameStore.game_state.players" 
        :key="player.id" 
        class="player-card"
        :class="{ 
          'is-current': player.id === gameStore.game_state.current_player_id,
          'is-dm': player.type === 'dm'
        }"
        @click="handleCardClick(player)"
      >
        <div class="player-header">
          <el-avatar :size="32" :src="getCharacterAvatar(player.public_info.character_name)"/>
          <div class="player-details">
            <span class="player-name">{{ player.name }}</span>
            <span class="character-name">{{ player.public_info.character_name }}</span>
          </div>
          <el-button v-if="player.type === 'dm'" type="primary" plain size="small" @click.stop="openDmChat(player)">私聊</el-button>
          <el-tag v-else :type="player.online ? 'success' : 'info'" size="small" class="status-tag">{{ player.online ? '在线' : '离线' }}</el-tag>
        </div>
      </el-card>
    </div>

    <!-- Player Details Dialog -->
    <el-dialog v-model="detailsDialogVisible" :title="`关于 “${selectedPlayer?.name}” 的信息`" width="550px">
      <div v-if="selectedPlayer" class="dialog-content-flex">
        <div class="dialog-character-portrait-left">
          <el-image 
            style="width: 180px; border-radius: 8px;"
            :src="getCharacterAvatar(selectedPlayer.public_info.character_name)" 
            fit="contain"
          />
        </div>

        <div class="relation-details-right">
          <!-- Ta 公开的信息 -->
          <div class="clues-section" style="margin-bottom: 16px;">
            <p><strong>Ta 公开的信息:</strong></p>
            <div v-if="publishedClues.length > 0">
              <el-tag v-for="clue in publishedClues" :key="clue" type="primary" class="clue-tag">{{ clue }}</el-tag>
            </div>
            <p v-else class="no-clues">暂无公开信息</p>
          </div>

          <!-- 你与 Ta 的关系 -->
          <div v-if="selectedPlayerRelation">
            <div class="relation-section">
              <p><strong>你与 Ta 的关系:</strong></p>
              <p class="relation-desc">{{ selectedPlayerRelation.desc }}</p>
            </div>
            <!-- 已移除关于 Ta 的公开线索展示 -->
          </div>
          <div v-else>
            <p>你对 Ta 暂无特殊认知。</p>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- DM Chat Dialog -->
    <el-dialog v-model="dmDialogVisible" title="与 DM 私聊" width="500px" class="dm-dialog">
       <div class="dm-chat-history">
          <div v-for="message in gameStore.dm_messages" :key="message.id" class="dm-message" :class="{'is-my-dm': message.from_id === gameStore.my_player_id}">
            <div class="dm-bubble">{{ message.content }}</div>
          </div>
       </div>
       <div class="dm-chat-input">
          <el-input v-model="dmInputText" placeholder="输入你想问的问题..." @keyup.enter="sendDmMessage"></el-input>
          <el-button type="primary" @click="sendDmMessage">发送</el-button>
       </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { UserFilled } from '@element-plus/icons-vue'
import { useGameStore } from '../store/gameStore.js'
import websocketService from '../services/websocketService.js'

const gameStore = useGameStore()
const detailsDialogVisible = ref(false)
const dmDialogVisible = ref(false)
const selectedPlayer = ref(null)
const selectedPlayerRelation = ref(null)
const publishedClues = ref([])
const dmInputText = ref('')

const getCharacterAvatar = (characterName) => {
  const mapping = {
    '船长': '/figure/洪船长.png',
    '二副': '/figure/张二副.png',
    '酒吧经理': '/figure/修经理.png',
    '乘务员': '/figure/韩乘务.png',
    '歌手': '/figure/林歌手.png',
    // DM and others can have a default or no avatar
  };
  return mapping[characterName] || ''; // Fallback to default avatar if not found
};

const handleCardClick = (player) => {
  if (player.type === 'dm') return;
  showPlayerDetails(player)
}

const showPlayerDetails = (player) => {
  if (player.id === gameStore.my_player_id) return // 不显示自己
  
  selectedPlayer.value = player
  const relation = gameStore.my_info.relationships.find(r => r.name.includes(player.public_info.character_name))
  selectedPlayerRelation.value = relation

  // 计算 Ta 公开的信息
  const clues = (gameStore.game_state.public_clues || [])
    .filter(c => c.publisher_id === player.id)
    .map(c => c.content)
  publishedClues.value = clues
  
  detailsDialogVisible.value = true
}

const openDmChat = (player) => {
  selectedPlayer.value = player
  dmDialogVisible.value = true
}

const sendDmMessage = () => {
  if(!dmInputText.value.trim()) return

  const message = {
    to: 'dm',
    content: dmInputText.value,
  }

  // 调用真实的服务发送消息
  const success = websocketService.sendDirectMessage(message)

  if (success) {
    // 发送成功后，立即将自己的消息添加到本地列表，以获得即时反馈
    gameStore.addDmMessage({
      from_id: gameStore.my_player_id,
      content: dmInputText.value,
      type: 'private'
    })
    dmInputText.value = ''
  }
}

</script>

<style scoped>
.public-info-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
}
.header {
  padding: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e8e8e8;
  flex-shrink: 0;
}
.player-list-container {
  overflow-y: auto;
  padding: 8px;
  flex-grow: 1;
}
.player-card {
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s ease-in-out;
}
.player-card:hover {
  transform: scale(1.02);
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.player-card.is-current {
  border-left: 4px solid #67C23A;
}
.player-card.is-dm {
  background-color: #fdf6ec;
}
.player-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.player-details {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}
.player-name {
  font-size: 14px;
  font-weight: 500;
}
.character-name {
  font-size: 12px;
  color: #909399;
}
.status-tag {
  flex-shrink: 0;
}
.dialog-content-flex {
  display: flex;
  gap: 20px;
}
.dialog-character-portrait-left {
  flex-shrink: 0;
}
.relation-details-right {
  flex-grow: 1;
}
.dialog-content p {
  line-height: 1.7;
}
.relation-desc {
  background-color: #f5f7fa;
  padding: 8px;
  border-radius: 4px;
}
.no-clues {
  color: #909399;
  font-size: 14px;
}
.clue-tag {
  margin: 4px;
}
.dm-dialog .el-dialog__body {
  padding: 10px 20px;
}
.dm-chat-history {
  height: 300px;
  overflow-y: auto;
  border: 1px solid #e8e8e8;
  padding: 10px;
  margin-bottom: 15px;
  border-radius: 4px;
}
.dm-message {
  margin-bottom: 10px;
  display: flex;
}
.is-my-dm {
  justify-content: flex-end;
}
.dm-bubble {
  max-width: 80%;
  padding: 8px 12px;
  border-radius: 8px;
  background-color: #f0f2f5;
  line-height: 1.5;
}
.is-my-dm .dm-bubble {
  background-color: #d9ecff;
}
.dm-chat-input {
  display: flex;
  gap: 10px;
}
</style> 