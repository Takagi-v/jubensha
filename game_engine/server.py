import asyncio
import json
import socketio
from aiohttp import web
from dm_agent import DMAgent
from player_agent import AIPlayerAgent
# ----------------- RAG 长时记忆初始化 -----------------
import os, time
from submodule.memory_rag.memory import RAGmanager

# 为每一局游戏创建独立的记忆目录（按时间戳区分）
_session_dir = os.path.join("rag_dbs", f"game_{int(time.time())}")
os.makedirs(_session_dir, exist_ok=True)

# 初始化 RAGmanager，并立即构建/加载索引
rag_manager = RAGmanager(save_path=_session_dir)
rag_manager.build_index()

# ----------------- Agents 初始化 -----------------
dm_agent = DMAgent(rag_manager=rag_manager)
ai_agents: dict[str, AIPlayerAgent] = {}

from script_content import CHARACTERS, CLUES, INITIAL_PROMPTS


# ----------------- AI Notification Helper (DEPRECATED) -----------------
# The new agent-based logic does not require broadcasting messages to AI players.
# They will fetch memories from the RAG manager when needed.

# ----------------- Socket.IO Server Setup -----------------
sio = socketio.AsyncServer(async_mode='aiohttp', cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

# ----------------- Game State Management -----------------
game_state = {
    "stage": "waiting_for_players",
    "players": {},
    "turn_order": [],
    "current_speaker_index": 0,
    "clues": {}, # Changed to dict for easier access
    "statements": {},
    "votes": {},
    "accusations": {},
    "public_clues": [],
    "messages": [], # To store chat history
    "pending_action": None
}

# Maps player_id to their socket_id (sid)
player_sids = {}

# ----------------- 阶段中文映射 -----------------
STAGE_LABELS = {
    "waiting_for_players": "等待玩家加入",
    "alibi": "不在场证明陈述",
    "investigation_1": "第一轮现场取证",
    "discussion_1": "第一轮推理陈述",
    "voting_1": "第一轮投票",
    "investigation_2": "第二轮现场取证",
    "discussion_2": "第二轮推理陈述",
    "final_accusation": "最终指认",
}


def translate_stage(stage_code: str) -> str:
    """将内部阶段代码转换为中文标签。"""
    return STAGE_LABELS.get(stage_code, stage_code)

# 在所有 emit 中统一使用
def stage_update_dict(stage_code: str):
    return {"current_stage": stage_code, "current_stage_label": translate_stage(stage_code)}

# ----------------- Helper: generate public game state -----------------
# 供前端刷新/重连时一次性同步当前公共信息
def build_public_game_state():
    current_player_id = (
        game_state["turn_order"][game_state["current_speaker_index"]]
        if game_state["turn_order"] and game_state["current_speaker_index"] < len(game_state["turn_order"]) else None
    )

    # --- 修复关键逻辑 ---
    # 如果当前玩家是 AI，且没有挂起的动作，则前端会因 pendingAction 为 null 而隐藏输入框，
    # 导致游戏看起来像是卡住了。我们强制给一个状态，让前端知道后台在运行。
    pending_action = game_state["pending_action"]
    if not pending_action and current_player_id and game_state["players"].get(current_player_id, {}).get("is_ai"):
        pending_action = "ai_thinking"


    public_state = {
        "current_stage": game_state["stage"],
        "current_stage_label": translate_stage(game_state["stage"]),
        "current_player_id": current_player_id,
        # 已移除 round 字段
        "turn_order": game_state["turn_order"],
        "pendingAction": pending_action,
        "players": [
            {
                "id": pid,
                "name": pinfo["name"],
                "type": ("dm" if pid == "dm" else ("ai" if pinfo["is_ai"] else "human")),
                "online": (pid in player_sids or pinfo["is_ai"]),
                "public_info": {"character_name": pinfo.get("character_name", pinfo["name"]), "status": "存活"}
            }
            for pid, pinfo in CHARACTERS.items()
        ]
    }
    return public_state

def initialize_game():
    """Initializes the game state and AI agents."""
    global ai_agents
    for player_id, player_info in CHARACTERS.items():
        game_state["players"][player_id] = {
            "id": player_id,
            "name": player_info["name"],
            "is_ai": player_info["is_ai"],
            "clues": []
        }
        if player_info["is_ai"] and player_id != 'dm':
             ai_agents[player_id] = AIPlayerAgent(
                 player_id=player_id,
                 role_name=player_info["name"],
                 rag_manager=rag_manager
             )

    print("Game initialized with players:", game_state["players"])
    print("AI agents initialized:", list(ai_agents.keys()))


def add_message(text, msg_type="system", author="系统", author_id="system"):
    """Adds a message to the game state, prints it to the console, and returns it."""

    import datetime

    # Frontend 期望的字段：from_id, from_name, content, type, timestamp
    message = {
        "from_id": author_id,
        "from_name": author,
        "content": text,
        "type": msg_type,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    game_state["messages"].append(message)
    # Print messages for debugging purposes
    print("--- MESSAGES UPDATED ---")
    # Pretty print the last 5 messages
    import json
    print(json.dumps(game_state["messages"][-5:], indent=2, ensure_ascii=False))
    print("------------------------")

    # -------- 将聊天内容写入 RAG 长时记忆 --------
    if msg_type == "chat":
        try:
            # 根据当前阶段推断轮次（0 代表尚未开始）
            round_num = 1 if "1" in game_state["stage"] else (2 if "2" in game_state["stage"] else 0)

            # 使用线程池避免阻塞事件循环
            # This is already async, no need to wrap in another task
            rag_manager.add_conversation_single(
                conversation_text=text,
                round_number=round_num,
                speakers=[author],
                timestamp=message["timestamp"]
            )
            print(rag_manager.list_history())
        except Exception as e:
            print(f"[RAG] 记录对话失败: {e}")

    return message

# No longer need give_clue_to_player, it's handled in the investigation stage directly

# ----------------- Game Flow and Logic -----------------
async def advance_game():
    """Drives the game forward based on the current state."""
    stage = game_state["stage"]
    print(f"Advancing game, current stage: {stage}")

    # The erroneous example code is now completely removed.

    if stage == "alibi":
        if game_state["current_speaker_index"] >= len(game_state["turn_order"]):
            # This is the correct place to transition the stage
            game_state["stage"] = "investigation_1"
            await sio.emit('game_state_update', stage_update_dict("investigation_1"))
            message = add_message("不在场证明陈述结束，进入现场取证阶段。")
            await sio.emit('new_message', message)
            asyncio.create_task(advance_game())
            return
        
        player_id = game_state["turn_order"][game_state["current_speaker_index"]]
        player = game_state["players"][player_id]
        
        # FIX: Add the missing state update for the current player
        await sio.emit('game_state_update', {"current_player_id": player_id})
        
        message = add_message(f"现在轮到 {player['name']} 发言。", msg_type="system", author_id=player_id)
        await sio.emit('new_message', message)

        if player["is_ai"]:
            try:
                # --- 发送正在输入状态 ---
                await sio.emit('player_typing', {'player_id': player_id, 'player_name': player['name']})
                print(f"--- Waiting for AI response from {player['name']} ({player_id}) for Introduction ---")
                
                agent = ai_agents.get(player_id)
                if agent:
                    statement = agent.act_and_respond("Introduction", "")
                else: # Fallback for DM or misconfigured agent
                    statement = f"轮到你了，{player['name']}。请陈述你的不在场证明。"

                print(f"--- Received AI response from {player['name']} ({player_id}) ---")

                game_state["statements"][player_id] = statement
                
                msg = add_message(statement, msg_type="chat", author=player["name"], author_id=player_id)
                await sio.emit('new_message', msg)
                # --- FIX: 清除正在输入状态 ---
                await sio.emit('player_done_typing', {'player_id': player_id})
                
                game_state["current_speaker_index"] += 1
                asyncio.create_task(advance_game())
            finally:
                # --- 保证无论如何都清除状态，以防中途出错 ---
                await sio.emit('player_done_typing', {'player_id': player_id})
        else:
            # For human players, set both state updates at once for atomicity
            game_state["pending_action"] = f"statement_{player_id}"
            await sio.emit('game_state_update', {
                "current_player_id": player_id,
                "pendingAction": game_state["pending_action"]
            })

    elif stage.startswith("investigation"):
        round_num_str = stage.split('_')[1] # "1" or "2"
        print(f"Starting investigation stage, round {round_num_str}...")
        
        round_clues_data = CLUES.get(f"round_{round_num_str}", {})
        if not round_clues_data:
            print(f"No clues found for round {round_num_str}.")
            # TODO: Handle this case
            return

        # Inform DM of all available clues this round
        all_clues_for_dm = [clue for clues_list in round_clues_data.values() for clue in clues_list]
        clues_summary = f"第 {round_num_str} 轮可公布的线索如下：\n" + "\n".join(all_clues_for_dm)
        dm_agent.handle_external_message(f"给 DM 的信息：\n{clues_summary}", should_respond=False)

        # Distribute clues to each player based on their character name key
        for player_id, player_info in game_state["players"].items():
            # Extract the key (first char of name, or full name)
            # e.g., '洪子廉 (你)' -> '洪'
            char_name_key = player_info["name"][0]
            
            player_clues = round_clues_data.get(char_name_key, [])
            
            if not player_clues:
                print(f"No clues found for player {player_id} with key '{char_name_key}' in round {round_num_str}")
                continue

            game_state["players"][player_id]["clues"].extend(player_clues)
            
            if player_info["is_ai"]:
                try:
                    await sio.emit('player_typing', {'player_id': player_id, 'player_name': player_info['name']})
                    print(f"--- Waiting for AI response from {player_info['name']} ({player_id}) for Sharing Clue ---")
                    agent = ai_agents.get(player_id)
                    if agent:
                        for clue in player_clues:
                            agent.receive_clue(clue)
                        
                        response = agent.act_and_respond("Sharing Clue", "")
                    else:
                        response = "我获得了一些线索，正在分析中。"
                    
                    print(f"--- Received AI response from {player_info['name']} ({player_id}) ---")
                    # 直接把 AI 的回复作为聊天气泡广播
                    chat_msg = add_message(response, msg_type="chat", author=player_info["name"], author_id=player_id)
                    await sio.emit('new_message', chat_msg)
                    # --- FIX: 清除正在输入状态 ---
                    await sio.emit('player_done_typing', {'player_id': player_id})

                    # 如果 AI 提到了“公开”，则把整段回复当作公开信息，存入 public_clues，
                    # 让前端在 other_info 中呈现
                    if response and "公开" in response:
                        game_state["public_clues"].append({
                            "publisher_id": player_id,
                            "publisher_name": player_info["name"],
                            "content": response
                        })
                        await sio.emit('game_state_update', {"public_clues": game_state["public_clues"]})
                finally:
                    # --- 保证无论如何都清除状态，以防中途出错 ---
                    await sio.emit('player_done_typing', {'player_id': player_id})
            else:
                # It's a human player, send them their batch of clues
                if player_id in player_sids:
                    await sio.emit('discovered_clues', {'clues': player_clues}, room=player_sids[player_id])

                    # 发送系统消息提示该玩家
                    sys_content = "你获得了以下线索：\n" + "\n".join([f"- {cl}" for cl in player_clues])
                    sys_msg = add_message(sys_content, msg_type="system")
                    await sio.emit('new_message', sys_msg, room=player_sids[player_id])

        await asyncio.sleep(2)
        # 更新内部阶段并广播
        next_stage = f"discussion_{round_num_str}"
        game_state["stage"] = next_stage
        await sio.emit('game_state_update', stage_update_dict(next_stage))
        message = add_message(f"第 {round_num_str} 轮现场取证结束，进入推理陈述阶段。")
        await sio.emit('new_message', message)
        game_state["turn_order"] = []
        game_state["current_speaker_index"] = 0
        game_state["statements"] = {}
        asyncio.create_task(advance_game())

    elif stage.startswith("discussion"):
        round_num = stage.split('_')[1]
        if not game_state["turn_order"]:
            dm_prompt = f"""
            现在进入第 {round_num} 轮推理陈述阶段。
            请你作为DM，为以下玩家决定一个合理的发言顺序。
            玩家列表 (id: 姓名): {json.dumps({pid: pinfo["name"] for pid, pinfo in game_state["players"].items() if pid != 'dm'}, ensure_ascii=False)}

            你的回复必须是一个严格的JSON对象，不要包含任何JSON格式之外的文字或你的思考过程。
            JSON格式如下:
            {{
              "turn_order": ["玩家ID_1", "玩家ID_2", ...],
              "announcement": "用你作为DM的口吻，向所有玩家宣布你为本轮推理制定的发言顺序。"
            }}
            请确保 "turn_order" 数组中的ID来自给定的玩家列表。
            """
            
            new_turn_order = []
            announcement_message = ""
            try:
                dm_response = dm_agent.handle_external_message(dm_prompt).strip()
                json_start = dm_response.find('{')
                json_end = dm_response.rfind('}') + 1
                if json_start != -1 and json_end != 0:
                    json_str = dm_response[json_start:json_end]
                    dm_data = json.loads(json_str)
                    potential_order = dm_data.get("turn_order", [])
                    announcement_message = dm_data.get("announcement", "")

                    valid_player_ids = set(game_state["players"].keys())
                    if potential_order and announcement_message and all(pid in valid_player_ids for pid in potential_order):
                        new_turn_order = potential_order
                    else:
                        raise ValueError("Invalid data from DM: missing fields or invalid player IDs.")
                else:
                    raise ValueError("No JSON object found in DM response.")

            except Exception as e:
                print(f"DM discussion turn order generation failed: {e}. Falling back to default.")
                new_turn_order = [pid for pid in game_state["players"] if pid != 'dm']
                order_text = " -> ".join([game_state["players"][pid]["name"] for pid in new_turn_order])
                announcement_message = f"本轮的发言顺序是: {order_text}"
            
            game_state["turn_order"] = new_turn_order
            game_state["current_speaker_index"] = 0
            await sio.emit('game_state_update', {"turn_order": game_state["turn_order"]})
            
            # --- Announce the turn order ---
            order_message = add_message(announcement_message, msg_type="chat", author="DM", author_id="dm")
            await sio.emit('new_message', order_message)

            # --- 立即启动下一次推进，而不是在本函数内继续执行 ---
            # 这给了前端一个处理状态更新的喘息机会
            asyncio.create_task(advance_game())
            return # 退出当前函数，避免重复执行

        if game_state["current_speaker_index"] >= len(game_state["turn_order"]):
            if round_num == "1":
                game_state["stage"] = "voting_1"
                await sio.emit('game_state_update', stage_update_dict("voting_1"))
                message = add_message("第一轮推理陈述结束，现在进入投票阶段。")
                await sio.emit('new_message', message)
            else: # round 2
                game_state["stage"] = "final_accusation"
                await sio.emit('game_state_update', stage_update_dict("final_accusation"))
                message = add_message("第二轮推理陈述结束，现在进入最终指认阶段。")
                await sio.emit('new_message', message)
            asyncio.create_task(advance_game())
            return
            
        # ----- Turn-based statement logic -----
        player_id = game_state["turn_order"][game_state["current_speaker_index"]]
        player = game_state["players"][player_id]

        await sio.emit('game_state_update', {"current_player_id": player_id})

        turn_msg = add_message(f"现在轮到 {player['name']} 发言。", msg_type="system", author_id="system")
        await sio.emit('new_message', turn_msg)

        if player["is_ai"]:
            try:
                await sio.emit('player_typing', {'player_id': player_id, 'player_name': player['name']})
                print(f"--- Waiting for AI response from {player['name']} ({player_id}) for Discussion ---")
                agent = ai_agents.get(player_id)
                if agent:
                    statement = agent.act_and_respond("Discussion", "")
                else: # Fallback for DM or misconfigured agent
                    statement = f"现在是推理陈述阶段（第 {round_num} 轮）。请 {player['name']} 表达你的推理观点。"
                
                print(f"--- Received AI response from {player['name']} ({player_id}) ---")
                game_state["statements"][player_id] = statement

                chat_msg = add_message(statement, msg_type="chat", author=player["name"], author_id=player_id)
                await sio.emit('new_message', chat_msg)
                # --- FIX: 清除正在输入状态 ---
                await sio.emit('player_done_typing', {'player_id': player_id})

                game_state["current_speaker_index"] += 1
                asyncio.create_task(advance_game())
            finally:
                # --- 保证无论如何都清除状态，以防中途出错 ---
                await sio.emit('player_done_typing', {'player_id': player_id})
        else:
            game_state["pending_action"] = f"statement_{player_id}"
            await sio.emit('game_state_update', {
                "current_player_id": player_id,
                "pendingAction": game_state["pending_action"]
            })

    elif stage == "voting_1":
        # ------------ AI 投票与发言 ------------
        import random
        for pid, pinfo in game_state["players"].items():
            if pid == 'dm' or not pinfo["is_ai"] or pid in game_state["votes"]:
                continue

            agent = ai_agents.get(pid)
            if agent:
                await sio.emit('player_typing', {'player_id': pid, 'player_name': pinfo['name']})
                try:
                    # AI Agent 现在直接返回结构化数据
                    vote_result = agent.vote()
                    
                    trust_id = vote_result["trust_id"]
                    suspect_id = vote_result["suspect_id"]
                    statement = vote_result["statement"]

                    # 记录投票，同时保存 AI 的解释性发言，便于前端展示
                    game_state["votes"][pid] = {
                        "trust": trust_id,
                        "suspect": suspect_id,
                        "statement": statement
                    }

                    # 将 AI 的发言作为角色聊天消息广播
                    await sio.emit('player_done_typing', {'player_id': pid})
                    ai_vote_msg = add_message(statement, msg_type="chat", author=pinfo['name'], author_id=pid)
                    await sio.emit('new_message', ai_vote_msg)

                except Exception as e:
                    print(f"Error processing AI vote for {pinfo['name']}: {e}")
                    # 即使 agent.vote() 内部有回退，这里也加一层保护
                    await sio.emit('player_done_typing', {'player_id': pid})

        
        # --- 后续流程 ---
        pending_votes = any(not p["is_ai"] and pid not in game_state["votes"] for pid, p in game_state["players"].items() if pid != 'dm')
        if pending_votes:
            game_state["pending_action"] = "vote"
            await sio.emit('game_state_update', {"pendingAction": game_state["pending_action"]})
        
        expected_voters = len([pid for pid in game_state["players"] if pid != 'dm'])
        if len(game_state["votes"]) >= expected_voters:
            # --- Notify DM of voting results ---
            vote_summary = "第一轮投票结果如下：\n"
            for voter_id, votes in game_state["votes"].items():
                voter_name = game_state["players"][voter_id]["name"]
                trust_name = game_state["players"][votes["trust"]]["name"]
                suspect_name = game_state["players"][votes["suspect"]]["name"]
                vote_summary += f"- {voter_name} 信任了 {trust_name}，怀疑了 {suspect_name}\n"
            
            dm_prompt = vote_summary + "\n请你基于此结果，为接下来的流程做准备。"
            dm_agent.handle_external_message(dm_prompt, should_respond=False)

            await sio.emit('game_state_update', {"votes": game_state["votes"]})
            
            # --- Reset state for next round ---
            game_state["stage"] = "investigation_2"
            game_state["pending_action"] = "" # Use empty string
            game_state["votes"] = {} # Clear votes for the next voting round (if any)
            
            await sio.emit('game_state_update', {
                "current_stage": "investigation_2",
                "current_stage_label": translate_stage("investigation_2"),
                "pendingAction": "", # Use empty string
                "votes": game_state["votes"]
            })
            
            message = add_message("第一轮投票结束，现在进入追加现场取证阶段。")
            await sio.emit('new_message', message)
            asyncio.create_task(advance_game())

    elif stage == "final_accusation":
        # --- AI Accusation Logic ---
        import random
        for pid, pinfo in game_state["players"].items():
            if not pinfo["is_ai"] or pid == 'dm' or pid in game_state["accusations"]:
                continue
            
            agent = ai_agents.get(pid)
            if agent:
                await sio.emit('player_typing', {'player_id': pid, 'player_name': pinfo['name']})
                try:
                    # AI Agent 现在直接返回结构化数据
                    accusation_result = agent.accuse()
                    accused_id = accusation_result["accused_id"]
                    statement = accusation_result["statement"]

                    # 记录指认
                    game_state["accusations"][pid] = {"accused": accused_id, "method": "无"} # method 暂时保留

                    # 将 AI 的发言作为角色聊天消息广播
                    await sio.emit('player_done_typing', {'player_id': pid})
                    accuse_msg = add_message(statement, msg_type="chat", author=pinfo['name'], author_id=pid)
                    await sio.emit('new_message', accuse_msg)

                except Exception as e:
                    print(f"Error processing AI accusation for {pinfo['name']}: {e}")
                    await sio.emit('player_done_typing', {'player_id': pid})
        
        pending_accusation = any(not p.get("is_ai", False) and pid not in game_state["accusations"] for pid, p in game_state["players"].items() if pid != 'dm')
        if pending_accusation:
            game_state["pending_action"] = "accuse"
            await sio.emit('game_state_update', {"pendingAction": game_state["pending_action"]})

        if len(game_state["accusations"]) == len([p for p in game_state["players"] if p != 'dm']):
            # --- All players have accused, start the reveal sequence ---
            accusation_summary = "最终指认结果如下：\n"
            for accuser_id, accusation in game_state["accusations"].items():
                accuser_name = game_state["players"][accuser_id]["name"]
                accused_name = game_state["players"][accusation["accused"]]["name"]
                accusation_summary += f"- {accuser_name} 指认了 {accused_name}\n"

            # 1. Notify DM and get the TRUTH (as a 'turn' message)
            truth_prompt = accusation_summary + "\n请基于此结果，公布最终的凶手和游戏真相！不要输出你的思考内容，直接作为DM输出真相就可以"
            truth_message = dm_agent.handle_external_message(truth_prompt)
            
            await sio.emit('game_state_update', {"accusations": game_state["accusations"]})
            
            final_truth_msg = add_message(truth_message, msg_type="turn", author="DM", author_id="dm")
            await sio.emit('new_message', final_truth_msg)

            await asyncio.sleep(5)  # Dramatic pause

            # 2. Ask DM for final RESULTS (as a 'turn' message)
            results_prompt = "现在请公布每位玩家的最终得分和游戏结局（谁是赢家，谁是输家）。需要根据游戏规则和玩家的表现来给出最终得分。请你作为游戏DM来回复，不要输出你的思考过程！"
            final_results_message = "计分板：游戏结束，感谢参与！"
            try:
                final_results_message = dm_agent.handle_external_message(results_prompt)
            except Exception as e:
                print(f"Error getting final results from DM: {e}")

            final_results_msg = add_message(final_results_message, msg_type="turn", author="DM", author_id="dm")
            await sio.emit('new_message', final_results_msg)

            # The game state is NOT set to 'game_over' here anymore.
            # The client will trigger it.


async def start_game_flow():
    """Initializes the first stage of the game."""
    print("Starting game flow...")
    game_state["stage"] = "alibi"
    await sio.emit('game_state_update', stage_update_dict("alibi"))
    # This message is sent to the frontend to indicate the stage start
    message = add_message("游戏进入第一阶段：不在场证明陈述。")
    await sio.emit('new_message', message)

    all_players = {pid: pinfo["name"] for pid, pinfo in game_state["players"].items() if pid != 'dm'}
    dm_prompt = f"""
    现在是游戏的第一阶段：不在场证明陈述。
    请你作为DM，为以下玩家决定一个合理的发言顺序。
    玩家列表 (id: 姓名): {json.dumps(all_players, ensure_ascii=False)}

    你的回复必须是一个严格的JSON对象，不要包含任何JSON格式之外的文字或你的思考过程。
    JSON格式如下:
    {{
      "turn_order": ["玩家ID_1", "玩家ID_2", ...],
      "announcement": "用你作为DM的口吻，向所有玩家宣布你制定的发言顺序。"
    }}
    请确保 "turn_order" 数组中的ID来自给定的玩家列表。
    """
    
    # --- Robust turn order generation for alibi stage ---
    new_turn_order = []
    announcement_message = ""
    try:
        dm_response = dm_agent.handle_external_message(dm_prompt).strip()
        # Find the JSON part of the response
        json_start = dm_response.find('{')
        json_end = dm_response.rfind('}') + 1
        if json_start != -1 and json_end != 0:
            json_str = dm_response[json_start:json_end]
            dm_data = json.loads(json_str)
            potential_order = dm_data.get("turn_order", [])
            announcement_message = dm_data.get("announcement", "")
            
            valid_player_ids = set(game_state["players"].keys())
            if potential_order and announcement_message and all(pid in valid_player_ids for pid in potential_order):
                new_turn_order = potential_order
            else:
                raise ValueError("Invalid data from DM: missing fields or invalid player IDs.")
        else:
            raise ValueError("No JSON object found in DM response.")

    except Exception as e:
        print(f"DM alibi turn order generation failed: {e}. Falling back to default.")
        # Fallback logic
        new_turn_order = [pid for pid in game_state["players"] if pid != 'dm']
        order_text = " -> ".join([game_state["players"][pid]["name"] for pid in new_turn_order])
        announcement_message = f"我已指定不在场证明的发言顺序: {order_text}"

    
    game_state["turn_order"] = new_turn_order
    game_state["current_speaker_index"] = 0
    
    await sio.emit('game_state_update', {"turn_order": game_state["turn_order"]})
    
    # --- Announce the turn order ---
    order_message = add_message(announcement_message, msg_type="chat", author="DM", author_id="dm")
    await sio.emit('new_message', order_message)

    print(f"DM has set the turn order: {game_state['turn_order']}")
    
    # This will immediately call advance_game to prompt the first speaker
    asyncio.create_task(advance_game())

async def send_current_state(sid):
    # 仅发送非空字段，避免把有效值覆盖成 null
    state_update = {
        "current_stage": game_state["stage"],
        "turn_order": game_state["turn_order"],
    }
    if game_state["turn_order"] and game_state["current_speaker_index"] < len(game_state["turn_order"]):
        state_update["current_player_id"] = game_state["turn_order"][game_state["current_speaker_index"]]
    if game_state["pending_action"]:
        state_update["pendingAction"] = game_state["pending_action"]

    await sio.emit('game_state_update', state_update, room=sid)

# ----------------- Socket.IO Event Handlers -----------------
@sio.event
async def connect(sid, environ):
    """Handle new client connections."""
    try:
        # The query string will be like: EIO=4&transport=websocket&sid=...&playerId=human_player_1
        query_dict = dict(item.split("=") for item in environ.get('QUERY_STRING', '').split("&") if "=" in item)
        player_id = query_dict.get('playerId')

        if not player_id or player_id not in CHARACTERS: # Check against CHARACTERS
            print(f"Connection rejected: Invalid player_id '{player_id}' from {sid}")
            await sio.emit('error', {'message': '无效的玩家ID'}, room=sid)
            return False
        
        player_sids[player_id] = sid
        player_name = CHARACTERS[player_id]['name']
        print(f"Player {player_id} ({player_name}) connected with sid: {sid}")

        # No longer sending initial_state. Frontend has it.
        # We just need to let the frontend know it's connected.
        # The frontend can set its 'is_connected' flag.
        # The 'connect' event on the client side handles this.
        
        message = add_message(f"玩家 {player_name} 已连接。")
        await sio.emit('new_message', message)
        
        # Check if this is the first human player connecting, and if so, start the game.
        human_players = [pid for pid, pinfo in CHARACTERS.items() if not pinfo['is_ai']]
        # If there's only one human player and this is them, start the game.
        if len(human_players) == 1 and player_id == human_players[0] and game_state["stage"] == "waiting_for_players":
            print("First human player connected. Starting game flow automatically.")
            asyncio.create_task(start_game_flow())

        # Send online status update AFTER potential game start, so stage is correct
        online_players_status = []
        for pid, p_info in CHARACTERS.items():
            # FIXING THE NameError: p_id -> pid
            online_players_status.append({"id": pid, "online": (pid in player_sids or p_info["is_ai"])})

        await sio.emit('game_state_update', { 'players': online_players_status })
        await send_current_state(sid)  # 补发重要字段

        # --- 发送完整初始状态（包含历史消息），保证刷新后仍能看到记录 ---
        initial_payload = {
            "gameState": build_public_game_state(),
            "messages": game_state["messages"]
        }
        await sio.emit('initial_state', initial_payload, room=sid)

    except Exception as e:
        print(f"Error in connect handler: {e}")


@sio.event
async def disconnect(sid, reason=None):
    """Handle client disconnections."""
    disconnected_player_id = None
    for player_id, player_sid in player_sids.items():
        if player_sid == sid:
            disconnected_player_id = player_id
            break
    
    if disconnected_player_id:
        del player_sids[disconnected_player_id]
        player_name = game_state['players'][disconnected_player_id]['name']
        print(f"Player {disconnected_player_id} ({player_name}) disconnected.")
        message = add_message(f"玩家 {player_name} 已断开连接。")
        await sio.emit('new_message', message)
        
        online_players_status = []
        for pid, p_info in CHARACTERS.items():
            # FIXING THE NameError: p_id -> pid
            online_players_status.append({"id": pid, "online": (pid in player_sids or p_info["is_ai"])})

        await sio.emit('game_state_update', {
            'players': online_players_status
        })


@sio.on('player_action')
async def handle_player_action(sid, action):
    """Handle actions from players."""
    player_id = None
    for pid, psid in player_sids.items():
        if psid == sid:
            player_id = pid
            break
    
    if not player_id:
        print(f"Action from unknown sid {sid}: {action}")
        return

    action_type = action.get("type")
    print(f"Received action '{action_type}' from player {player_id}: {action}")

    # Map frontend actions to backend game flow
    if action_type == "start_game" and game_state["stage"] == "waiting_for_players":
        asyncio.create_task(start_game_flow())

    elif action_type == "submit_statement" and game_state["pending_action"] == f"statement_{player_id}":
        # Correctly extract the statement from the payload object
        payload = action.get("payload", {})
        statement = payload.get("statement", "")
        
        game_state["statements"][player_id] = statement
        
        message = add_message(statement, msg_type="chat", author=game_state["players"][player_id]["name"], author_id=player_id)
        await sio.emit('new_message', message)

        game_state["pending_action"] = "" # Use empty string
        game_state["current_speaker_index"] += 1
        asyncio.create_task(advance_game())

    elif action_type == "publish_clue":
        clue_to_publish = action.get("payload")
        player = game_state["players"][player_id]
        clue_content = clue_to_publish['content']
        
        # Add to public clues state and broadcast
        game_state["public_clues"].append({
            "publisher_id": player_id,
            "publisher_name": player["name"],
            "content": clue_content
        })
        await sio.emit('game_state_update', {"public_clues": game_state["public_clues"]})

        # Send system message to all players
        message = add_message(f"{player['name']} 公开了线索：\n{clue_content}", msg_type="system")
        await sio.emit('new_message', message)
    
    elif action_type == "submit_vote" and game_state["pending_action"] == "vote":
        voter_id = player_id
        payload = action.get("payload", {})
        trust_vote = payload.get("trust")
        suspect_vote = payload.get("suspect")

        if voter_id not in game_state["votes"]:
            # 前端可额外传入 statement 字段（对投票理由的解释），如无则留空
            statement = payload.get("statement", "")
            game_state["votes"][voter_id] = {
                "trust": trust_vote,
                "suspect": suspect_vote,
                "statement": statement
            }
            message = add_message(f"玩家 {game_state['players'][voter_id]['name']} 已完成投票。", msg_type="system")
            await sio.emit('new_message', message)
           
            # 广播更新后的投票状态
            await sio.emit('game_state_update', {"votes": game_state["votes"]})
            
            asyncio.create_task(advance_game())

    elif action_type == "submit_accusation" and game_state["pending_action"] == "accuse":
        accuser_id = player_id
        payload = action.get("payload", {})
        accused_id = payload.get("accused_id")

        if accuser_id not in game_state["accusations"]:
            game_state["accusations"][accuser_id] = {"accused": accused_id, "method": "无"}
            message = add_message(f"玩家 {game_state['players'][accuser_id]['name']} 已完成最终指认。")
            await sio.emit('new_message', message)

            # No longer notifying DM here, it will be done in batch at the end.

            await sio.emit('game_state_update', {"accusations": game_state["accusations"]})
            asyncio.create_task(advance_game())


@sio.on('direct_message')
async def handle_private_message_to_dm(sid, data):
    """Handles private messages from a player to the DM."""
    player_id = None
    for pid, psid in player_sids.items():
        if psid == sid:
            player_id = pid
            break

    if not player_id:
        print(f"Private message from unknown sid {sid}: {data}")
        return

    player_name = game_state['players'].get(player_id, {}).get('name', '未知玩家')
    question = data.get('content', '')

    print(f"Received private message from {player_name} ({player_id}) for DM: '{question}'")

    if not question:
        return # Ignore empty messages

    dm_response = dm_agent.whisper(player_id, question)

    # Create the response message payload
    import datetime
    response_message = {
        "from_id": "dm",
        "from_name": "DM",
        "content": dm_response,
        "type": "private",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

    # Send the DM's response back only to the originating player
    await sio.emit('dm_message', response_message, room=sid)
    print(f"Sent private response from DM to {player_name} ({player_id}).")


# ----------------- Main Application Runner -----------------
if __name__ == '__main__':
    initialize_game()
    print("Starting Socket.IO server on http://localhost:8765")
    web.run_app(app, host='localhost', port=8765) 