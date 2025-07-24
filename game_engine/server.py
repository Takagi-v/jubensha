import asyncio
import socketio
from aiohttp import web

from ai_test import get_ai_response
# ----------------- 新增：线程池包装 -----------------
async def get_ai_response_async(prompt: str):
    """在后台线程执行阻塞式 get_ai_response，避免阻塞事件循环。"""
    return await asyncio.to_thread(get_ai_response, prompt)
from script_content import CHARACTERS, CLUES, INITIAL_PROMPTS

# ----------------- AI Notification Helper -----------------
async def notify_ai_players(statement_author_id: str, statement_text: str):
    """让所有 AI（排除自己和 DM）获取最新发言，方便后续推理。"""
    for pid, pinfo in game_state["players"].items():
        # 仅通知 AI（包括 DM），跳过发言者本人
        if not pinfo.get("is_ai"):
            continue
        if pid == statement_author_id:
            continue  # 不必通知自己

        # 这里仅做测试：直接把发言作为上下文发给 get_ai_response
        # 真正部署时可换成长上下文、知识库或流式更新接口
        prompt = (
            f"最新发言来自 {game_state['players'][statement_author_id]['name']}：\n"
            f"\"{statement_text}\"\n"
            "请你记住这段信息，用于之后的讨论（无需回复）。"
        )
        try:
            _ = await get_ai_response_async(prompt)
        except Exception as e:
            print(f"Error notifying AI {pid}: {e}")



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

# ----------------- Helper: generate public game state -----------------
# 供前端刷新/重连时一次性同步当前公共信息
def build_public_game_state():
    public_state = {
        "current_stage": game_state["stage"],
        "current_player_id": (
            game_state["turn_order"][game_state["current_speaker_index"]]
            if game_state["turn_order"] and game_state["current_speaker_index"] < len(game_state["turn_order"]) else None
        ),
        "round": 1 if "1" in game_state["stage"] else (2 if "2" in game_state["stage"] else 0),
        "turn_order": game_state["turn_order"],
        "pendingAction": game_state["pending_action"],
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
    """Initializes the game state with players from script_content."""
    for player_id, player_info in CHARACTERS.items():
        game_state["players"][player_id] = {
            "id": player_id,
            "name": player_info["name"],
            "is_ai": player_info["is_ai"],
            "clues": []
        }
    print("Game initialized with players:", game_state["players"])

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
            await sio.emit('game_state_update', {"current_stage": "investigation_1"})
            message = add_message("不在场证明陈述结束，进入现场取证阶段。")
            await sio.emit('new_message', message)
            asyncio.create_task(advance_game())
            return
        
        player_id = game_state["turn_order"][game_state["current_speaker_index"]]
        player = game_state["players"][player_id]
        
        # FIX: Add the missing state update for the current player
        await sio.emit('game_state_update', {"current_player_id": player_id})
        
        message = add_message(f"现在轮到 {player['name']} 发言。", msg_type="turn", author_id=player_id)
        await sio.emit('new_message', message)

        if player["is_ai"]:
            ai_prompt = INITIAL_PROMPTS.get(player_id, f"轮到你了，{player['name']}。请陈述你的不在场证明。")
            statement = await get_ai_response_async(ai_prompt)
            game_state["statements"][player_id] = statement
            
            msg = add_message(statement, msg_type="chat", author=player["name"], author_id=player_id)
            await sio.emit('new_message', msg)

            # 通知其它 AI 该发言
            await notify_ai_players(player_id, statement)
            
            game_state["current_speaker_index"] += 1
            asyncio.create_task(advance_game())
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
        await get_ai_response_async(f"给 DM 的信息：\n{clues_summary}")

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
                ai_clues_str = "\n".join(player_clues)
                ai_prompt = (
                    f"你进入了搜证阶段，获得了以下专属线索：\n{ai_clues_str}\n"
                    "如果你想公开其中的部分或全部线索，请在你的回复中自行说明，并直接附上你要公开的线索内容。"
                )
                response = await get_ai_response_async(ai_prompt)

                # 直接把 AI 的回复作为聊天气泡广播
                chat_msg = add_message(response, msg_type="chat", author=player_info["name"], author_id=player_id)
                await sio.emit('new_message', chat_msg)

                # 如果 AI 提到了“公开”，则把整段回复当作公开信息，存入 public_clues，
                # 让前端在 other_info 中呈现
                if "公开" in response:
                    game_state["public_clues"].append({
                        "publisher_id": player_id,
                        "publisher_name": player_info["name"],
                        "content": response
                    })
                    await sio.emit('game_state_update', {"public_clues": game_state["public_clues"]})
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
        await sio.emit('game_state_update', {"current_stage": next_stage})
        message = add_message(f"第 {round_num_str} 轮现场取证结束，进入推理陈述阶段。")
        await sio.emit('new_message', message)
        game_state["turn_order"] = []
        game_state["current_speaker_index"] = 0
        game_state["statements"] = {}
        asyncio.create_task(advance_game())

    elif stage.startswith("discussion"):
        round_num = stage.split('_')[1]
        if not game_state["turn_order"]:
            dm_prompt = f"现在进入第 {round_num} 轮推理陈述阶段，请给出合理的发言顺序。"
            
            new_turn_order = []
            try:
                dm_response = (await get_ai_response_async(dm_prompt)).strip()
                if dm_response:
                    # Filter out any empty strings that might result from splitting
                    potential_order = [pid.strip() for pid in dm_response.replace("，", ",").split(',') if pid.strip()]
                    
                    # Validate the generated order
                    valid_player_ids = set(game_state["players"].keys())
                    if all(pid in valid_player_ids for pid in potential_order):
                        new_turn_order = potential_order
                    else:
                        print(f"DM-provided turn order is invalid: {potential_order}. Falling back to default.")
            except Exception as e:
                print(f"DM turn order generation failed with error: {e}")

            # If the process failed or resulted in an empty list, use a default order
            if not new_turn_order:
                print("Using default turn order.")
                # Default order: all players except DM
                new_turn_order = [pid for pid in game_state["players"] if pid != 'dm']
            
            game_state["turn_order"] = new_turn_order
            game_state["current_speaker_index"] = 0
            await sio.emit('game_state_update', {"turn_order": game_state["turn_order"]})
            
            # --- Announce the turn order ---
            order_text = " -> ".join([game_state["players"][pid]["name"] for pid in new_turn_order])
            order_message = add_message(f"DM 指定了发言顺序: {order_text}", msg_type="system")
            await sio.emit('new_message', order_message)

        if game_state["current_speaker_index"] >= len(game_state["turn_order"]):
            if round_num == "1":
                game_state["stage"] = "voting_1"
                await sio.emit('game_state_update', {"current_stage": "voting_1"})
                message = add_message("第一轮推理陈述结束，现在进入投票阶段。")
                await sio.emit('new_message', message)
            else: # round 2
                game_state["stage"] = "final_accusation"
                await sio.emit('game_state_update', {"current_stage": "final_accusation"})
                message = add_message("第二轮推理陈述结束，现在进入最终指认阶段。")
                await sio.emit('new_message', message)
            asyncio.create_task(advance_game())
            return
            
        # ----- Turn-based statement logic -----
        player_id = game_state["turn_order"][game_state["current_speaker_index"]]
        player = game_state["players"][player_id]

        await sio.emit('game_state_update', {"current_player_id": player_id})

        turn_msg = add_message(f"现在轮到 {player['name']} 发言。", msg_type="turn", author_id="system")
        await sio.emit('new_message', turn_msg)

        if player["is_ai"]:
            ai_prompt = (
                f"现在是推理陈述阶段（第 {round_num} 轮）。请 {player['name']} 表达你的推理观点。"
            )
            statement = await get_ai_response_async(ai_prompt)
            game_state["statements"][player_id] = statement

            chat_msg = add_message(statement, msg_type="chat", author=player["name"], author_id=player_id)
            await sio.emit('new_message', chat_msg)

            await notify_ai_players(player_id, statement)

            game_state["current_speaker_index"] += 1
            asyncio.create_task(advance_game())
        else:
            game_state["pending_action"] = f"statement_{player_id}"
            await sio.emit('game_state_update', {
                "current_player_id": player_id,
                "pendingAction": game_state["pending_action"]
            })

    elif stage == "voting_1":
        # ------------ AI 投票 ------------
        import random
        for pid, pinfo in game_state["players"].items():
            if pid == 'dm':
                continue  # DM 不参与投票
            if not pinfo["is_ai"]:
                continue
            if pid in game_state["votes"]:
                continue
            # 简单策略：随机信任一个、怀疑一个（且不相同）
            other_ids = [k for k in game_state["players"].keys() if k != pid]
            trust = random.choice(other_ids)
            suspect = random.choice([x for x in other_ids if x != trust])
            game_state["votes"][pid] = {"trust": trust, "suspect": suspect}
            ai_vote_msg = add_message(f"{pinfo['name']} 已完成投票。", msg_type="system")
            await sio.emit('new_message', ai_vote_msg)
        
        pending_votes = any(not p["is_ai"] and pid not in game_state["votes"] for pid, p in game_state["players"].items())
        if pending_votes:
            game_state["pending_action"] = "vote"
            await sio.emit('game_state_update', {"pendingAction": game_state["pending_action"]})
        
        if len(game_state["votes"]) == len(game_state["players"]):
            # --- Notify DM of voting results ---
            vote_summary = "第一轮投票结果如下：\n"
            for voter_id, votes in game_state["votes"].items():
                voter_name = game_state["players"][voter_id]["name"]
                trust_name = game_state["players"][votes["trust"]]["name"]
                suspect_name = game_state["players"][votes["suspect"]]["name"]
                vote_summary += f"- {voter_name} 信任了 {trust_name}，怀疑了 {suspect_name}\n"
            
            dm_prompt = vote_summary + "\n请你基于此结果，为接下来的流程做准备。"
            try:
                await get_ai_response_async(dm_prompt)
            except Exception as e:
                print(f"Error notifying DM of vote results: {e}")

            await sio.emit('game_state_update', {"votes": game_state["votes"]})
            
            # --- Reset state for next round ---
            game_state["stage"] = "investigation_2"
            game_state["pending_action"] = "" # Use empty string
            game_state["votes"] = {} # Clear votes for the next voting round (if any)
            
            await sio.emit('game_state_update', {
                "current_stage": "investigation_2",
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
            if not pinfo["is_ai"] or pid == 'dm':
                continue
            if pid in game_state["accusations"]:
                continue
            
            # Simple strategy: AI asks for who to accuse
            other_players_str = ", ".join([p["name"] for p in game_state["players"].values() if p["id"] != pid and p["id"] != 'dm'])
            ai_prompt = (
                f"你是 {pinfo['name']}，现在是最终指认环节。"
                f"你认为谁是凶手？请从以下玩家中选择一个进行指认：{other_players_str}"
            )
            
            try:
                response = await get_ai_response_async(ai_prompt)
                # Find the player ID that matches the response name
                accused_id = next((p_id for p_id, p in game_state["players"].items() if p["name"] in response), None)
                if not accused_id:
                    # Fallback to random if name not found
                    accused_id = random.choice([p_id for p_id in game_state["players"] if p_id != pid and p_id != 'dm'])
            except Exception:
                accused_id = random.choice([p_id for p_id in game_state["players"] if p_id != pid and p_id != 'dm'])

            game_state["accusations"][pid] = {"accused": accused_id, "method": "无"}
            accuse_msg = add_message(f"玩家 {pinfo['name']} 已完成最终指认。", msg_type="system")
            await sio.emit('new_message', accuse_msg)
        
        pending_accusation = any(not p.get("is_ai", False) and pid not in game_state["accusations"] for pid, p in game_state["players"].items())
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
            truth_prompt = accusation_summary + "\n请基于此结果，公布最终的凶手和游戏真相！"
            truth_message = "游戏结束！"
            try:
                truth_message = await get_ai_response_async(truth_prompt)
            except Exception as e:
                print(f"Error getting game over message from DM: {e}")
                # Fallback to find the real killer from script_content
                from script_content import PLAYER_SCRIPTS
                real_killer_name = ""
                for pid, script in PLAYER_SCRIPTS.items():
                    if "你是船上的毒贩" in "".join(script.get("secrets", [])):
                         real_killer_name = CHARACTERS[pid]['name']
                         break
                truth_message = f"游戏结束！凶手是 {real_killer_name}。"
            
            await sio.emit('game_state_update', {"accusations": game_state["accusations"]})
            
            final_truth_msg = add_message(truth_message, msg_type="turn", author="DM", author_id="dm")
            await sio.emit('new_message', final_truth_msg)

            await asyncio.sleep(5)  # Dramatic pause

            # 2. Ask DM for final RESULTS (as a 'turn' message)
            results_prompt = "现在请公布每位玩家的最终得分和游戏结局（谁是赢家，谁是输家）。"
            final_results_message = "计分板：游戏结束，感谢参与！"
            try:
                final_results_message = await get_ai_response_async(results_prompt)
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
    await sio.emit('game_state_update', {"current_stage": "alibi"})
    # This message is sent to the frontend to indicate the stage start
    message = add_message("游戏进入第一阶段：不在场证明陈述。")
    await sio.emit('new_message', message)

    dm_prompt = INITIAL_PROMPTS["dm"]
    
    # --- Robust turn order generation for alibi stage ---
    new_turn_order = []
    try:
        dm_response = (await get_ai_response_async(dm_prompt)).strip()
        if dm_response:
            potential_order = [pid.strip() for pid in dm_response.replace("，", ",").split(',') if pid.strip()]
            valid_player_ids = set(game_state["players"].keys())
            if all(pid in valid_player_ids for pid in potential_order):
                new_turn_order = potential_order
            else:
                print(f"DM-provided alibi turn order is invalid: {potential_order}. Falling back to default.")
    except Exception as e:
        print(f"DM alibi turn order generation failed with error: {e}")

    if not new_turn_order:
        print("Using default alibi turn order.")
        new_turn_order = [pid for pid in game_state["players"] if pid != 'dm']
    
    game_state["turn_order"] = new_turn_order
    game_state["current_speaker_index"] = 0
    
    await sio.emit('game_state_update', {"turn_order": game_state["turn_order"]})
    
    # --- Announce the turn order ---
    order_text = " -> ".join([game_state["players"][pid]["name"] for pid in new_turn_order])
    order_message = add_message(f"DM 指定了发言顺序: {order_text}", msg_type="system")
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

        # 通知其它 AI 该发言
        await notify_ai_players(player_id, statement)

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
            game_state["votes"][voter_id] = {"trust": trust_vote, "suspect": suspect_vote}
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

    # Construct a prompt for the DM AI
    prompt = (
        f"一名玩家（{player_name}）正在私下问你问题。\n"
        f"请你扮演好DM的角色，根据游戏当前进展（如有）和他交流，但绝对不要泄露任何尚未公开的线索、秘密或凶手信息。\n"
        f"玩家的问题是：\n"
        f"\"{question}\""
    )

    dm_response = "DM现在有点忙，稍后再试吧。" # Default response
    try:
        # Assuming get_ai_response is synchronous for now, as used elsewhere
        dm_response = await get_ai_response_async(prompt)
    except Exception as e:
        print(f"Error getting DM AI response for {player_id}: {e}")

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