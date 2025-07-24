# 剧本杀 AI Demo

这是一个使用 Vue 3, Vite, Element Plus, Socket.IO 和 Python 构建的在线剧本杀游戏 Demo。其中，游戏逻辑和 AI 玩家由后端 Python 服务器驱动。

## 项目结构

- `src/`: 前端 Vue 项目源码
- `public/`: 前端静态资源，如图片等
- `game_engine/`: 后端 Python 游戏引擎
  - `server.py`: Socket.IO 服务器主文件
  - `script_content.py`: 游戏脚本、角色、线索等内容
  - `ai_test.py`: 对接大语言模型的 AI 玩家逻辑
  - `requirements.txt`: Python 依赖项

## 技术栈

- **前端**: Vue 3 (Composition API), Vite, Element Plus, Pinia, Socket.IO Client
- **后端**: Python, aiohttp, python-socketio, openai

## 环境配置与启动

### 1. 前端

确保你已安装 [Node.js](https://nodejs.org/) (版本 >= 16.0.0)。

```bash
# 进入项目根目录
cd jubensha

# 安装依赖
npm install

# 启动 Vite 开发服务器
npm run dev
```

启动后，在浏览器中打开 `http://localhost:5173` 即可访问。

### 2. 后端

后端使用 Python 运行。建议使用虚拟环境。

```bash
# 进入游戏引擎目录
cd game_engine

# (可选，但推荐) 创建并激活虚拟环境
python -m venv venv
# Windows
# venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端服务器
python server.py
```

后端服务器会运行在 `http://localhost:8765`。前端应用会自动连接到此地址。

**注意**:
- 前后端需要同时运行。
- AI 功能 (在 `ai_test.py` 中) 可能需要配置 API Key 等环境变量，请根据你的实际情况进行设置。 