import { io } from 'socket.io-client'
import { useGameStore } from '../store/gameStore'

class WebsocketService {
  constructor() {
    this.socket = null
  }

  connect(playerId) {
    // 防止重复连接
    if (this.socket && this.socket.connected) {
      console.log('已经连接，无需重复操作')
      return
    }

    // 从 Pinia store 获取 gameStore 实例
    // 注意：这需要在 Pinia 初始化之后调用
    const gameStore = useGameStore()

    // 后端服务器地址
    // The backend server is running on port 8765
    const VITE_APP_WS_URL = import.meta.env.VITE_APP_WS_URL || 'http://localhost:8765'
    
    console.log(`正在连接到 ${VITE_APP_WS_URL}...`)
    this.socket = io(VITE_APP_WS_URL, {
      query: {
        playerId,
      },
      transports: ['websocket'],
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    })

    // 监听连接成功
    this.socket.on('connect', () => {
      console.log('✅ WebSocket 连接成功! Socket ID:', this.socket.id)
      gameStore.setConnectionStatus(true)
    })

    // 监听连接错误
    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket 连接错误:', error.message)
      gameStore.setConnectionStatus(false)
    })

    // 监听断开连接
    this.socket.on('disconnect', (reason) => {
      console.warn('🔌 WebSocket 连接断开:', reason)
      gameStore.setConnectionStatus(false)
    })

    // 注册核心事件监听器
    this.registerEventListeners(gameStore)
  }

  registerEventListeners(gameStore) {
    // 监听来自后端的初始状态
    this.socket.on('initial_state', ({ gameState, myInfo, messages }) => {
      console.log('接收到 initial_state:', { gameState, myInfo, messages })
      if (gameState) gameStore.setGameState(gameState)
      if (myInfo) gameStore.setMyInfo(myInfo)
      if (messages) gameStore.setMessages(messages) // 需要在 store 中添加 setMessages action
    })

    // 监听游戏公共状态更新
    this.socket.on('game_state_update', (newGameState) => {
      console.log('接收到 game_state_update:', newGameState)
      gameStore.setGameState(newGameState)
      // 调试: 打印合并后的完整 game_state
      console.log('%c[GameStore] 当前 game_state', 'color: #42b983; font-weight: bold;',
                  JSON.parse(JSON.stringify(gameStore.game_state)))
    })

    // 监听新消息
    this.socket.on('new_message', (newMessage) => {
      console.log('接收到 new_message:', newMessage)
      gameStore.addMessage(newMessage)
    })
    
    // 监听私密信息更新
     this.socket.on('private_update', (newPrivateInfo) => {
      console.log('接收到 private_update:', newPrivateInfo)
      gameStore.setMyInfo(newPrivateInfo)
    })
    
    // 监听来自DM的私聊消息
    this.socket.on('dm_message', (newMessage) => {
      console.log('接收到 dm_message:', newMessage)
      gameStore.addDmMessage(newMessage)
    })

    // Listen for a batch of clues discovered by the player
    this.socket.on('discovered_clues', ({ clues }) => {
        console.log('接收到 discovered_clues:', clues)
        gameStore.addDiscoveredClues(clues)
    })
  }
  
  sendAction(action) {
    if (!this.socket || !this.socket.connected) {
      console.error('无法发送动作：WebSocket 未连接')
      return false
    }
    this.socket.emit('player_action', action)
    console.log('发送动作:', action)
    return true
  }

  sendDirectMessage(message) {
    if (!this.socket || !this.socket.connected) {
      console.error('无法发送私聊：WebSocket 未连接')
      return false
    }
    this.socket.emit('direct_message', message)
    console.log('发送私聊:', message)
    return true
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
}

export default new WebsocketService() 