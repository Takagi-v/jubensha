import { io } from 'socket.io-client'
import { useGameStore } from '../store/gameStore.js'

class WebsocketService {
  socket = null
  store = null

  connect(playerId) {
    // DEV: 'http://localhost:8765'
    // PROD: window.location.host
    this.socket = io('http://localhost:8765', {
      query: { playerId },
      transports: ['websocket'],
      upgrade: false,
    })

    this.store = useGameStore()

    this.socket.on('connect', () => {
      console.log('WebSocket connected successfully.')
      this.store.setConnectionStatus(true)
    })

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason)
      this.store.setConnectionStatus(false)
    })

    this.socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err)
    })

    this.socket.on('initial_state', (payload) => {
      console.log('Received initial state for reconnection:', payload)
      // 使用新的 action 来原子化地更新整个 store
      this.store.setInitialState(payload);
    })

    this.socket.on('game_state_update', (newState) => {
      console.log('Game state updated:', newState)
      this.store.setGameState(newState)
    })

    this.socket.on('new_message', (newMessage) => {
      console.log('New message received:', newMessage)
      this.store.addMessage(newMessage)
    })
    
    this.socket.on('dm_message', (newMessage) => {
        console.log('New DM message received:', newMessage)
        this.store.addDmMessage(newMessage)
    })

    this.socket.on('discovered_clues', (data) => {
        console.log("Discovered new clues: ", data.clues)
        this.store.addDiscoveredClues(data.clues)
    })
    
    // --- 新增：监听正在输入事件 ---
    this.socket.on('player_typing', (data) => {
        console.log(`${data.player_name} is typing...`)
        this.store.setPlayerTyping(data.player_id, data.player_name, true)
    })

    this.socket.on('player_done_typing', (data) => {
        console.log(`${data.player_name} is done typing.`)
        this.store.setPlayerTyping(data.player_id, data.player_name, false)
    })

    this.socket.on('error', (error) => {
      console.error('Received error from server:', error)
      // Optionally, display this error to the user
      alert(`发生错误: ${error.message}`)
    })
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
    }
  }

  sendAction(actionType, payload) {
    if (!this.socket || !this.socket.connected) {
      console.error('Socket not connected.')
      return false
    }
    const action = { type: actionType, payload }
    console.log('Sending action:', action)
    this.socket.emit('player_action', action)
    return true
  }

  sendDirectMessage(message) {
    if (!this.socket || !this.socket.connected) {
      console.error('Socket not connected for DM.')
      return false
    }
    console.log('Sending DM:', message)
    this.socket.emit('direct_message', message)
    return true
  }
}

export default new WebsocketService() 