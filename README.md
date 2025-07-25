# 剧本杀 AI Demo

这是一个使用 Vue 3, Vite, Element Plus, Socket.IO 和 Python 构建的在线剧本杀游戏 Demo。其中，游戏逻辑和 AI 玩家由后端 Python 服务器驱动。

## 游戏概述与剧情背景

**东方之星号豪华游轮谋杀案**

一艘正在公海航行的豪华游轮上，大副 **刘奇** 被发现死于货物仓库。船上六名主要船员被临时封锁，船长与众人决定展开一场真人版“剧本杀”调查，以找出凶手、动机与作案手法。

- 时间线：2015 年 5 月 13 日 20:00 — 船上举行烟花表演期间。
- 死者信息：刘奇，东方之星号大副，死因枪伤伴随不明化学灼伤。
- 凶案特点：烟花声掩盖枪响、仓库内部出现可疑硫酸饮料瓶及细长刺伤痕。
- 游戏目标：所有玩家根据线索与对话推理真凶；凶手则需混淆视听、掩盖罪行。

> 本项目将上述线下推理脚本数字化，并融合大语言模型扮演 DM 与 AI 玩家，实现 **人机同桌推理** 的沉浸式体验。

### 角色列表
| 编号 | 身份 | 是否 AI | 角色简介 | 初始立场 |
| ---- | ---- | ------- | -------- | -------- |
| human_player_1 | 洪子廉·船长 (你) | 否 | 新任船长，外表正直，暗中走私 | 找出凶手并避免被怀疑 |
| ai_player_1 | 张文远·二副 | 是 | 学历最高的船员，对死者晋升心怀不满 | 自证清白 |
| ai_player_2 | 修仁杰·酒吧经理 | 是 | 真凶；负责酒吧，对毒品交易心生恐惧 | 掩盖罪行并嫁祸他人 |
| ai_player_3 | 韩亦暮·乘务员 | 是 | 八卦好奇心强，曾被死者长期使唤 | 自证清白 |
| ai_player_4 | 林若彤·歌手 | 是 | 歌手，欠债被死者胁迫约会 | 自证清白并保护船长恋情 |
| dm | 游戏主持人 | 是 | 负责节奏控制与发布系统讯息 | 公正推进流程 |

> 每个角色拥有「公开身份介绍 + 不在场证明 + 私密秘密/关系 + 专属线索」。凶手可说谎，其他人禁止说谎但可选择性隐瞒。

### 完整游戏流程
1. **等待玩家加入**：前端大厅展示房间，至少一名真人加入即开局。
2. **不在场证明陈述 (alibi)**  
   - DM 随机/智能指定发言顺序。  
   - 玩家依次做自我介绍与当晚行踪说明。
3. **第一轮现场取证 (investigation_1)**  
   - 系统向不同角色分发私有线索；AI 玩家自动阅读并可能公开部分发现。  
   - 关键地点：仓库、各船员房间、酒吧、操舵室等。
4. **第一轮推理陈述 (discussion_1)**  
   - DM 再次给出发言顺序。  
   - 玩家结合线索进行公开讨论，提出怀疑。
5. **第一轮投票 (voting_1)**  
   - 玩家匿名投信任/怀疑票；若票数集中可直接结束，否则继续。
6. **第二轮现场取证 (investigation_2)**  
   - 再次分发更深层线索，例如财务记录、伤口细节、隐藏武器等。
7. **第二轮推理陈述 (discussion_2)**
8. **最终指认 (final_accusation)**  
   - 所有玩家公开指认真凶并说明理由。  
   - 系统结算，公布真凶、得分与彩蛋解析。

流程中的每一步都通过 Socket.IO 实时广播到前端；AI 角色或 DM 发言时会先发送 "typing" 状态以模拟思考，再输出自然语言内容。

## 项目结构

- `src/`: 前端 Vue 项目源码
- `public/`: 前端静态资源，如图片等
- `game_engine/`: 后端 Python 游戏引擎
  - `server.py`: Socket.IO 服务器主文件，包含主要的游戏流程逻辑
  - `dm_agent.py`: “剧本主持人” (DM) 角色的大语言模型逻辑
  - `player_agent.py`: AI 玩家角色逻辑
  - `script_content.py`: 游戏脚本、角色、线索等内容
  - `submodule/memory_rag/`: 基于 RAG 的长时记忆子模块
  - `requirements.txt`: Python 核心依赖项

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

# 安装核心依赖
pip install -r requirements.txt

# 安装 Memory RAG 子模块依赖（启用长时记忆功能时必需）
pip install -r submodule/memory_rag/requirements.txt

# 启动后端服务器
python server.py
```

后端服务器会运行在 `http://localhost:8765`。前端应用会自动连接到此地址。

**注意**:
- 前后端需要同时运行。
- 运行 AI 代理（DM 与 AI 玩家）需要有效的 `OPENAI_API_KEY` 环境变量，可通过 `export OPENAI_API_KEY=你的Key` 设置。 