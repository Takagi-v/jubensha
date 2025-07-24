<template>
  <div class="my-info-panel">
    <div class="header">
      <el-icon><Avatar /></el-icon>
      <span>我的档案</span>
    </div>
    <div class="content-wrapper">
      <el-menu :default-active="activeMenu" class="side-menu" @select="handleMenuSelect">
        <el-menu-item index="basic"><el-icon><Postcard /></el-icon><span>基本信息</span></el-menu-item>
        <el-menu-item index="secrets"><el-icon><Lock /></el-icon><span>秘密任务</span></el-menu-item>
        <el-menu-item index="relations"><el-icon><Connection /></el-icon><span>人际关系</span></el-menu-item>
        <el-menu-item index="timeline"><el-icon><Clock /></el-icon><span>时间线</span></el-menu-item>
        <el-menu-item index="other_info"><el-icon><InfoFilled /></el-icon><span>持有信息</span></el-menu-item>
      </el-menu>
      
      <div class="info-display-area">
        <div v-if="gameStore.my_info">
          <!-- 基本信息 -->
          <div v-show="activeMenu === 'basic'" class="info-content-item">
            <el-descriptions :column="1" border size="small">
              <el-descriptions-item label="姓名">{{ myInfo.character.name }}</el-descriptions-item>
              <el-descriptions-item label="简介">{{ myInfo.character.description }}</el-descriptions-item>
              <el-descriptions-item label="我的陈述">{{ myInfo.statement }}</el-descriptions-item>
            </el-descriptions>
          </div>
          <!-- 秘密任务 -->
          <div v-show="activeMenu === 'secrets'" class="info-content-item">
            <el-alert v-for="secret in myInfo.secrets" :key="secret" :title="secret" type="warning" :closable="false" class="info-item"/>
          </div>
          <!-- 人际关系 -->
          <div v-show="activeMenu === 'relations'" class="info-content-item">
            <el-collapse accordion>
              <el-collapse-item v-for="rel in myInfo.relationships" :key="rel.name" :title="rel.name">
                <div>{{ rel.desc }}</div>
                <div v-if="rel.clues && rel.clues.length > 0" class="relation-clues">
                  <strong>相关线索:</strong>
                  <el-tag v-for="clue in rel.clues" :key="clue" class="clue-tag" style="margin: 2px;">{{ clue }}</el-tag>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
          <!-- 时间线 -->
          <div v-show="activeMenu === 'timeline'" class="info-content-item">
            <el-timeline style="padding-left: 10px;">
              <el-timeline-item v-for="item in myInfo.timeline" :key="item.time" :timestamp="item.time" size="small">
                {{ item.event }}
              </el-timeline-item>
            </el-timeline>
          </div>
          <!-- 持有信息 -->
          <div v-show="activeMenu === 'other_info'" class="info-content-item">
             <div v-for="info in myInfo.other_info" :key="info" class="other-info-item" v-html="formatOtherInfo(info)"></div>
          </div>
        </div>
        <el-empty v-else description="暂无私密信息"></el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { Avatar, Postcard, Lock, Connection, Clock, InfoFilled } from '@element-plus/icons-vue'
import { useGameStore } from '../store/gameStore.js'

const gameStore = useGameStore()
const activeMenu = ref('basic')

const handleMenuSelect = (index) => {
  activeMenu.value = index
}

// Use the new getter to ensure data is always up-to-date with public clues
const myInfo = computed(() => gameStore.my_info_with_public_clues);

const formatOtherInfo = (info) => {
  return info.replace(/---(.*?)---/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
};
</script>

<style scoped>
.my-info-panel {
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
.content-wrapper {
  display: flex;
  flex-grow: 1;
  overflow: hidden;
}
.side-menu {
  width: 120px;
  flex-shrink: 0;
  border-right: 1px solid #e8e8e8;
}
.info-display-area {
  flex-grow: 1;
  padding: 16px;
  overflow-y: auto;
}
.info-content-item {
  font-size: 14px;
  line-height: 1.6;
}
.info-item {
  margin-bottom: 10px;
}
</style> 