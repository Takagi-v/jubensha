<template>
  <div class="my-info-panel">
    <el-card shadow="never" class="info-card">
      <template #header>
        <div class="card-header">
          <el-icon><Avatar /></el-icon>
          <span>我的信息</span>
        </div>
      </template>
      <el-tabs v-model="activeTab" v-if="gameStore.my_info">
        <el-tab-pane label="角色" name="character">
          <div class="tab-content" v-if="gameStore.my_info.character">
            <h3>{{ gameStore.my_info.character.name }}</h3>
            <p>{{ gameStore.my_info.character.description }}</p>
          </div>
        </el-tab-pane>
        <el-tab-pane label="背景" name="background">
          <div class="tab-content">
            <p>{{ gameStore.my_info.background }}</p>
          </div>
        </el-tab-pane>
        <el-tab-pane label="任务" name="objectives">
          <div class="tab-content">
            <el-timeline>
              <el-timeline-item v-for="(obj, index) in gameStore.my_info.objectives" :key="index" :timestamp="`任务 ${index + 1}`">
                {{ obj }}
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>
        <el-tab-pane label="线索" name="clues">
          <div class="tab-content">
             <el-empty v-if="!gameStore.my_info.private_clues || gameStore.my_info.private_clues.length === 0" description="暂无线索"></el-empty>
             <div v-else class="clue-list">
                <el-tag v-for="(clue, index) in gameStore.my_info.private_clues" :key="index" type="success">{{ clue }}</el-tag>
             </div>
          </div>
        </el-tab-pane>
      </el-tabs>
      <el-empty v-else description="暂无私密信息"></el-empty>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Avatar } from '@element-plus/icons-vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
const activeTab = ref('character')
</script>

<style scoped>
.my-info-panel {
  padding: 16px;
  height: 100%;
  box-sizing: border-box;
}
.info-card {
  height: 100%;
  border: none;
}
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.tab-content {
  padding: 8px;
  line-height: 1.6;
}
h3 {
  margin-top: 0;
}
.clue-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style> 