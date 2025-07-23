import { defineStore } from 'pinia'

export const useGameStore = defineStore('game', {
  // 核心状态 (State)
  state: () => ({
    welcomeSequenceCompleted: false, // 新增状态
    my_player_id: 'human_player_1',
    is_connected: false,
    
    // 从后端同步的公开游戏信息
    game_state: {
      current_stage: '讨论阶段',
      current_player_id: 'human_player_1',
      round: 2,
      players: [
        {
          id: 'human_player_1',
          name: '玩家1 (你)',
          type: 'human',
          online: true,
          public_info: { character_name: '管家', status: '存活' },
        },
        {
          id: 'ai_player_1',
          name: 'AI-医生',
          type: 'ai',
          online: true,
          public_info: { character_name: '医生', status: '存活' },
        },
        {
          id: 'ai_player_2',
          name: 'AI-律师',
          type: 'ai',
          online: true,
          public_info: { character_name: '律师', status: '嫌疑' },
        },
        {
          id: 'ai_player_3',
          name: 'AI-富商',
          type: 'ai',
          online: false,
          public_info: { character_name: '富商', status: '已死亡' },
        },
      ]
    },
    
    // 只属于当前玩家的私密信息
    my_info: {
       character: {
        name: '忠诚的管家',
        description: '您是这座庄园的管家，对主人忠心耿耿。您知道庄园内的很多秘密。',
      },
      background: '您在这座庄园工作了20年，见证了主人家族的兴衰。昨晚的宴会上发生了命案，您必须找出真凶，同时保护家族的秘密。',
      objectives: [
        '保护主人的名誉',
        '找出真正的凶手',
        '避免家族秘密被曝光',
      ],
      private_clues: [
        '主人的保险柜密码',
        '昨晚看到可疑身影',
      ],
    },
    
    // 聊天消息列表
    messages: [
      { id: 1, type: 'system', content: '游戏开始！请各位玩家开始讨论。', timestamp: new Date(Date.now() - 60000 * 5) },
      { id: 2, type: 'normal', from_id: 'ai_player_1', from_name: 'AI-医生', content: '各位，我们需要冷静分析现场的证据。我先去检查一下尸体。', timestamp: new Date(Date.now() - 60000 * 4) },
      { id: 3, type: 'normal', from_id: 'ai_player_2', from_name: 'AI-律师', content: '同意，医生，请务必仔细。管家先生，你最后一次见到死者是什么时候？', timestamp: new Date(Date.now() - 60000 * 3) },
      { id: 4, type: 'normal', from_id: 'human_player_1', from_name: '管家 (你)', content: '大约是在晚餐后，他回到书房去了。我没有再见过他。', timestamp: new Date(Date.now() - 60000 * 2) },
      { id: 5, type: 'system', content: '医生搜查了书房，发现了一封带血的信。', timestamp: new Date(Date.now() - 60000 * 1) },
    ],
  }),

  // 核心计算属性 (Getters)
  getters: {
    // 是否轮到我行动
    is_my_turn(state) {
      return state.game_state?.current_player_id === state.my_player_id
    },
    // 获取当前玩家对象
    current_player(state) {
        if (!state.game_state?.players || !state.game_state?.current_player_id) return null
        return state.game_state.players.find(p => p.id === state.game_state.current_player_id)
    }
  },

  // 核心动作 (Actions)
  actions: {
    setConnectionStatus(status) {
      this.is_connected = status
    },
    setGameState(newState) {
      this.game_state = newState
    },
    setMyInfo(newInfo) {
      this.my_info = newInfo
    },
    addMessage(newMessage) {
      this.messages.push({
        id: Date.now() + Math.random(),
        timestamp: new Date(),
        ...newMessage
      })
    },
    setMessages(messages) {
      this.messages = messages
    },
    // 新增 action
    completeWelcomeSequence() {
      this.welcomeSequenceCompleted = true
    },
  }
}) 