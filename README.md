# 剧本杀游戏前端Demo

这是一个基于Vue 3 + Vite + Pinia + Element Plus构建的剧本杀游戏前端演示项目。

## ✨ 功能特性

- 🎮 **实时游戏体验**: 通过WebSocket与后端实时通信
- 🤖 **AI + 真人混合**: 支持AI玩家和真人玩家同时游戏
- 💬 **即时聊天**: 实时聊天系统，支持系统消息和玩家对话
- 🎭 **角色扮演**: 完整的角色信息、背景故事和私密线索系统
- 🎯 **多种行动**: 支持搜查、调查、移动、指控等游戏动作
- 📱 **响应式设计**: 适配桌面和移动端设备
- 🎨 **现代UI**: 使用Element Plus构建的美观界面

## 🛠️ 技术栈

- **前端框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **状态管理**: Pinia
- **UI组件库**: Element Plus
- **实时通信**: Socket.IO Client
- **样式**: CSS3 + Element Plus主题

## 📁 项目结构

```
src/
├── components/          # 组件目录
│   ├── StatusBar.vue    # 状态栏组件
│   ├── ChatPanel.vue    # 聊天面板
│   ├── MyInfoPanel.vue  # 个人信息面板
│   ├── PublicInfoPanel.vue # 公共信息面板
│   └── ActionInput.vue  # 行动输入组件
├── store/
│   └── gameStore.js     # 游戏状态管理
├── services/
│   └── websocketService.js # WebSocket通信服务
├── App.vue              # 主应用组件
├── main.js              # 应用入口
└── style.css            # 全局样式
```

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

项目将在 `http://localhost:3000` 启动。

### 构建生产版本

```bash
npm run build
```

## 🎯 核心设计思路

### 1. 状态管理中心 (Pinia Store)
- `my_player_id`: 当前玩家ID
- `game_state`: 游戏公共状态
- `my_info`: 玩家私密信息
- `messages`: 聊天消息列表
- `is_connected`: 连接状态

### 2. WebSocket通信层
- 自动连接到后端游戏服务器
- 监听游戏状态更新、消息、私密信息变化
- 发送玩家行动到后端

### 3. 响应式UI组件
- 所有组件都从Store读取数据
- 纯展示组件，不包含复杂逻辑
- 自动响应状态变化并重新渲染

### 4. 用户交互系统
- 只有轮到玩家时才能进行操作
- 支持多种游戏动作（搜查、调查、移动、指控）
- 实时聊天和系统通知

## 🎮 游戏界面说明

### 状态栏
- 显示连接状态
- 当前游戏阶段
- 当前行动玩家

### 左侧面板 - 个人信息
- 角色身份和背景
- 任务目标
- 私密线索
- 其他重要信息

### 中间区域 - 聊天和行动
- 实时聊天消息
- 快捷行动按钮
- 聊天输入框

### 右侧面板 - 公共信息
- 所有玩家状态
- 游戏统计信息
- 玩家在线状态

## 🔧 配置说明

### WebSocket连接
默认连接到 `http://localhost:8000`，可在 `src/services/websocketService.js` 中修改。

### 玩家ID
默认玩家ID为 `human_player_1`，可在启动时配置。

## 🐛 调试功能

项目内置调试面板，包含：
- 连接状态信息
- 发送测试消息
- 模拟游戏状态
- 实时状态监控

点击左下角的设置按钮可开启/关闭调试面板。

## 📝 注意事项

1. **后端依赖**: 此前端需要配合对应的后端服务使用
2. **浏览器兼容**: 建议使用现代浏览器 (Chrome 90+, Firefox 88+, Safari 14+)
3. **网络连接**: 确保后端服务正常运行在8000端口
4. **实时性**: 游戏依赖WebSocket连接，请确保网络稳定

## 🎨 自定义样式

项目使用Element Plus主题，可通过以下方式自定义：

1. 修改 `src/style.css` 中的全局样式
2. 在组件中使用scoped样式
3. 覆盖Element Plus的CSS变量

## 📄 License

MIT License 