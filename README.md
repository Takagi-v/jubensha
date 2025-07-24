# 剧本杀游戏Demo

这是一个基于Vue 3 (前端) 和 Python (后端) 构建的全栈剧本杀游戏演示项目。

## ✨ 功能特性

- 🎮 **实时游戏体验**: 通过WebSocket与后端实时通信，实现状态同步。
- 🤖 **AI + 真人混合**: 支持AI玩家和真人玩家同场竞技。
- 💬 **公共与私密聊天**:
    - **公共频道**: 所有玩家可见的实时聊天系统，支持系统消息和玩家对话。
    - **与DM私聊**: 玩家可随时与AI DM进行一对一私聊，获取非剧透的游戏提示。
- 🎭 **角色扮演**: 完整的角色信息、背景故事、秘密任务和私密线索系统。
- 🔍 **多阶段游戏流程**: 包含不在场证明、搜证、讨论、投票、最终指认等经典剧本杀环节。
- 📱 **响应式设计**: 适配桌面和移动端设备。
- 🎨 **现代UI**: 使用Element Plus构建的美观、清晰的界面。

## 🛠️ 技术栈

- **前端**: Vue 3 (Composition API), Vite, Pinia, Element Plus, Socket.IO Client
- **后端**: Python, aiohttp, python-socketio
- **AI (模拟)**: 使用大语言模型接口进行对话生成 (当前为模拟实现)。

## 📁 项目结构

```
jubensha/
├── game_engine/         # 后端游戏引擎
│   ├── server.py        # Socket.IO 服务器
│   ├── ai_test.py       # AI 模型接口 (模拟)
│   └── script_content.py # 游戏脚本内容
├── src/                 # 前端源码
│   ├── components/      # UI 组件
│   ├── store/           # Pinia 状态管理
│   ├── services/        # 服务层 (WebSocket)
│   ├── App.vue          # 主应用组件
│   ├── main.js          # 应用入口
│   └── style.css        # 全局样式
└── README.md
```

## 🚀 快速开始

确保你的开发环境已安装 [Node.js](https://nodejs.org/) (v16+) 和 [Python](https://www.python.org/) (v3.8+)。

### 1. 后端设置

a. **进入后端目录并创建虚拟环境** (推荐):
```bash
cd game_engine
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

b. **安装Python依赖**:
```bash
pip install "python-socketio[aiohttp]"
# AI 功能依赖于一个外部的 LLM API，在 ai_test.py 中配置
```

c. **启动后端服务器**:
```bash
# 在项目根目录运行
python game_engine/server.py
```
后端服务将在 `http://localhost:8765` 启动。

### 2. 前端设置

a. **安装NPM依赖** (在项目根目录):
```bash
npm install
```

b. **启动开发服务器**:
```bash
npm run dev
```
前端开发服务器通常会运行在 `http://localhost:5173` (具体端口见终端输出)。在浏览器中打开此地址即可开始游戏。

### 3. 构建生产版本

```bash
npm run build
```

## 🎯 核心设计思路 (前端)

### 1. 状态管理中心 (Pinia Store)
- `my_player_id`: 当前玩家ID
- `game_state`: 游戏公共状态
- `my_info`: 玩家私密信息
- `messages`: 公共聊天消息列表
- `dm_messages`: 与DM的私聊消息列表
- `is_connected`: WebSocket连接状态

### 2. WebSocket通信层
- 自动连接到后端游戏服务器 (`http://localhost:8765`)。
- 监听游戏状态更新、新消息、私密信息等事件。
- 封装 `sendAction` 和 `sendDirectMessage` 方法向后端发送玩家动作和消息。

## 🎮 游戏界面说明

### 状态栏 (顶部)
- **阶段**: 显示当前游戏阶段，如 `alibi`, `investigation_1` 等。
- **当前玩家**: 显示正在行动的玩家。
- **回合**: 显示当前游戏回合。

### 左侧面板 - 我的档案
- 查看个人角色身份、任务目标、秘密、时间线等私密信息。

### 中间区域 - 聊天面板
- 显示所有公共聊天消息和系统通知。
- 底部的输入框用于在你的回合进行发言。

### 右侧面板 - 公共信息
- 显示所有玩家的状态（在线/离线）。
- 点击DM玩家卡片上的 **[私聊]** 按钮，可以向AI DM提问。

## 📝 注意事项

1. **服务启动顺序**: 建议先启动后端服务，再启动前端服务。
2. **网络端口**: 确保端口 `8765` (后端) 和 `5173` (前端，或其他) 未被占用。
3. **浏览器兼容**: 建议使用现代浏览器 (Chrome, Firefox, Safari, Edge的最新版本)。
4. **AI配置**: 当前AI为模拟实现，如需对接真实模型，请修改 `game_engine/ai_test.py` 中的 `get_ai_response` 函数。

## 📄 License

MIT License 