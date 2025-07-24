import { defineStore } from 'pinia'

export const useGameStore = defineStore('game', {
  // 核心状态 (State)
  state: () => ({
    welcomeSequenceCompleted: false, // 新增状态
    my_player_id: 'human_player_1',
    is_connected: false,
    
    // 从后端同步的公开游戏信息
    game_state: {
      current_stage: '等待游戏开始', // More neutral initial state
      current_player_id: null, // More neutral initial state
      round: 0,
      players: [
        {
          id: 'human_player_1',
          name: '洪子廉 (你)',
          type: 'human',
          online: true,
          public_info: { character_name: '船长', status: '存活' },
        },
        {
          id: 'ai_player_1',
          name: '张文远',
          type: 'ai',
          online: true,
          public_info: { character_name: '二副', status: '存活' },
        },
        {
          id: 'ai_player_2',
          name: '修仁杰',
          type: 'ai',
          online: true,
          public_info: { character_name: '酒吧经理', status: '存活' },
        },
        {
          id: 'ai_player_3',
          name: '韩亦暮',
          type: 'ai',
          online: true,
          public_info: { character_name: '乘务员', status: '存活' },
        },
        {
          id: 'ai_player_4',
          name: '林若彤',
          type: 'ai',
          online: true,
          public_info: { character_name: '歌手', status: '存活' },
        },
        {
          id: 'dm',
          name: '游戏管理员 (DM)',
          type: 'dm',
          online: true,
          public_info: { character_name: 'DM', status: '在线' },
        },
      ],
      votes: {}, // 新增：存储投票结果
      accusations: {}, // 新增：存储指认结果
      public_clues: [], // 新增：存储所有公开线索
    },
    
    // 只属于当前玩家的私密信息（船长角色）
    my_info: {
      character: {
        name: '洪子廉 (船长)',
        description: '男，38岁，国内海洋大学毕业。你已经在船上工作12年，1年前前船长意外死亡后，你成为了东方之星号的新主人。这里所有人都得听你的。',
      },
      statement: '刘奇是我的学弟，我很照顾他。烟花表演20点开始，我到甲板看表演。20点15分，我想起有话要对刘大副说，就去了他常在的仓库。20点25分左右，我到了仓库，然后就发现了他……我是第一发现者。',
      secrets: [
        '你和歌手林若彤是秘密恋人关系。',
        '你与韩国黑道“三合会”有联系，利用游轮偷偷运输毒品。你负责对接，而死者刘奇负责具体执行。',
      ],
      relationships: [
        { name: '刘奇 (大副)', desc: '你的大学学弟，被你一手提拔，是你走私毒品的手下。', clues: ['已死亡。'] },
        { name: '张文远 (二副)', desc: '国际航海学校毕业，文凭比你高，对刘奇的晋升心怀不满，曾向你打小报告但被你无视了。', clues: ['他的房间里发现了一双带泥的鞋子。'] },
        { name: '修仁杰 (酒吧经理)', desc: '2年前上船，与你交集不多。', clues: [] },
        { name: '韩亦暮 (乘务员)', desc: '你因她与林若彤吵架而罚她写了检讨书。', clues: ['有人听到她在案发时间附近与人发生激烈争吵。'] },
        { name: '林若彤 (歌手)', desc: '酒吧的歌手，也是你的秘密恋人，你昵称她为“小黄莺”。', clues: [] },
      ],
      timeline: [
        { time: '18:40', event: '你接到餐厅电话，是说出大事了，你赶去餐厅，是看到张二副跪在船上最尊贵的客人 (VVIP) 面前，因为 VVIP 有花生过敏症，而张三副把花生冰淇淋拿给了她。张二副被要求下跪道歉，你立马也道歉了，带着张二副走了。你把这个事情汇报给了董事会。' },
        { time: '19:40', event: '你收到三合会的传真，是一些塔罗牌，内容是船长，秘密交易，背叛，碰面，港口，杀。你也不是非常确定里面的内容，你猜测是三合会警告你如果敢背叛，就会杀了你。所以决定一会去问问刘奇。你把塔罗牌藏在了了你设有密码的箱子里，箱子放在操舵室的暗格里。' },
        { time: '20:00', event: '看到恋人林若彤穿着被扯坏的演出服回到她的房间。随后你去甲板观看烟花表演。' },
        { time: '20:15', event: '你知道刘奇一般都会在航行结束前去仓库整理东西，所以觉得他在仓库。决定去仓库找他' },
        { time: '20:25', event: '到达仓库，发现刘奇已经死了。' },
      ],
      other_info: [
        '你知道张二副是负责管理枪支的，几乎所有人都知道操舵室里有把左轮枪。',
        '你有一把私人的手枪和一些子弹藏在你的房间里，用来防范毒品运输中存在的危险。',
        '你最近送了一条项链给林若彤。',
        '你有烟瘾，但在船上只能用尼古丁液抽电子烟。',
      ],
      objectives: [
        '查明大副刘奇的死因。',
        '在游轮到港前找到凶手。',
        '防止船上发生大规模恐慌。',
        '隐瞒你的所有秘密。',
      ],
      rules: [
        '你的目的是与大家共同合作找出本案的凶手，但同时要注意避免自己被怀疑。',
        '犯人是场上唯一一个可以说谎的人，你不能说谎，但可以隐瞒掉一些对自己不利的证据。',
        '在游戏刚开始时也请少提供信息，以免让犯人获得过多用于编造事实的情报。',
        '计分规则为：每有一个人在第一轮投票中对你投出信任票 +10 分，每有一个人在第一轮投票中对你投出怀疑票 -10 分，每有一个人在最后投票指证你为犯人 -20 分，你指证对犯人 + 50 分，同时成功推理出犯案手法 + 50 分。'
      ]
    },
    
    // 聊天消息列表
    messages: [
      { id: 1, type: 'system', content: '东方之星号谋杀案，调查开始。', timestamp: new Date() },
    ],

    // 与DM的私聊消息
    dm_messages: [
      { id: 'dm_1', from_id: 'dm', from_name: 'DM', content: '你好，船长。如果在规则或剧情上有任何疑问，可以随时在这里向我提问。', type: 'dm' },
    ],
    // To store clues discovered during the investigation phases
    discovered_clues: [],
  }),

  // 核心计算属性 (Getters)
  getters: {
    // 是否轮到我行动
    is_my_turn(state) {
      // 投票或指认阶段，轮到所有未行动的人类玩家
      if (state.game_state?.pendingAction === 'vote') {
        const myPlayer = state.game_state.players.find(p => p.id === state.my_player_id);
        return myPlayer && myPlayer.type === 'human' && !state.game_state.votes[state.my_player_id];
      }
      if (state.game_state?.pendingAction === 'accuse') {
        const myPlayer = state.game_state.players.find(p => p.id === state.my_player_id);
        return myPlayer && myPlayer.type === 'human' && !state.game_state.accusations[state.my_player_id];
      }
      // 其他阶段，按当前发言人判断
      return state.game_state?.current_player_id === state.my_player_id;
    },
    // 获取当前玩家对象
    current_player(state) {
        if (!state.game_state?.players || !state.game_state?.current_player_id) return null
        return state.game_state.players.find(p => p.id === state.game_state.current_player_id)
    },

    // 动态计算整合了公开线索的人际关系
    my_info_with_public_clues(state) {
      if (!state.my_info || !state.my_info.relationships) return state.my_info;

      const new_my_info = JSON.parse(JSON.stringify(state.my_info));
      
      const public_clues_by_publisher_name = (state.game_state.public_clues || []).reduce((acc, clue) => {
        // Use a simple includes check on the character name part
        const publisher_char_name = clue.publisher_name.split(' ')[0];
        if (!acc[publisher_char_name]) {
          acc[publisher_char_name] = [];
        }
        acc[publisher_char_name].push(`Ta公开的线索: ${clue.content}`);
        return acc;
      }, {});

      for (const rel of new_my_info.relationships) {
        // Match if the relationship name includes the publisher's character name
        const publisher_name_to_find = Object.keys(public_clues_by_publisher_name).find(p_name => rel.name.includes(p_name));
        if (publisher_name_to_find) {
          // Avoid duplicating clues
          const existing_clues = new Set(rel.clues);
          const new_clues = public_clues_by_publisher_name[publisher_name_to_find];
          for(const new_clue of new_clues){
            if(!existing_clues.has(new_clue)){
              rel.clues.push(new_clue);
            }
          }
        }
      }

      // Append all public clues to 'other_info' as a formatted string array
      if (state.game_state.public_clues && state.game_state.public_clues.length > 0) {
        if (!new_my_info.other_info) {
          new_my_info.other_info = [];
        }
        
        const section_title = "--- 已公开的公共线索 ---";
        const formatted_public_clues = state.game_state.public_clues.map(c => 
            `[${c.publisher_name} 公开] ${c.content}`
        );
        
        let existing_section_index = new_my_info.other_info.findIndex(item => typeof item === 'string' && item.startsWith(section_title));

        const new_section = [section_title, ...formatted_public_clues].join('\n');

        if (existing_section_index !== -1) {
            new_my_info.other_info[existing_section_index] = new_section;
        } else {
            new_my_info.other_info.push(new_section);
        }
      }
      return new_my_info;
    }
  },

  // 核心动作 (Actions)
  actions: {
    setConnectionStatus(status) {
      this.is_connected = status
    },
    setGameState(newState) {
      // 只合并非空字段，避免服务端空值覆盖已有数据
      const filtered = Object.fromEntries(
        Object.entries(newState).filter(([, v]) => v !== null && v !== undefined)
      )

      // 特殊处理 players 深合并，保持名称 / public_info 等不被覆盖
      if (filtered.players && Array.isArray(filtered.players)) {
        const playersMap = Object.fromEntries(this.game_state.players.map(p => [p.id, { ...p }]))
        for (const upd of filtered.players) {
          if (!playersMap[upd.id]) {
            playersMap[upd.id] = { ...upd }
          } else {
            playersMap[upd.id] = { ...playersMap[upd.id], ...upd }
          }
        }
        filtered.players = Object.values(playersMap)
      }

      // Ensure public_clues is always an array
      if (filtered.public_clues && !Array.isArray(filtered.public_clues)) {
        filtered.public_clues = [];
      }
      this.game_state = { ...this.game_state, ...filtered }
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
    addDmMessage(newMessage) {
      this.dm_messages.push({
        id: Date.now() + Math.random(),
        ...newMessage
      })
    },
    // Action to add a new clue to the player's private info
    addClueToMyInfo(clue) {
      // This action is now obsolete, we will use addDiscoveredClues instead.
      // For backward compatibility, let's just push to the new array.
      this.discovered_clues.push(clue.content);
    },
    // New action to handle a list of clues
    addDiscoveredClues(clues) {
        this.discovered_clues.push(...clues);
    },
    completeWelcomeSequence() {
      this.welcomeSequenceCompleted = true
    },
  }
}) 