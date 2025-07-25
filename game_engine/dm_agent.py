import os
import json
import requests
from typing import Dict, Any, List, Optional, Callable
from submodule.memory_rag.memory import RAGmanager

class DMAgent:
    def __init__(self, rag_manager: RAGmanager, model_name: str = "gemini-2.5-flash"):
        self.rag_manager = rag_manager
        self.api_url = "https://api.xi-ai.cn/v1/chat/completions"
        # 警告：为了测试，密钥暂时硬编码。在生产环境中，请务必使用环境变量或安全的密钥管理方式。
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer"
        }
        self.model = model_name

        self.system_prompt = f'''你是一个剧本杀的DM，负责引导游戏流程。你是一名经验丰富的、公平公正的剧本杀游戏主持人（DM）。请注意，你的任务是确保游戏的顺利进行，而不是直接参与游戏。你需要根据剧本内容和玩家的行为，做出合理的判断和回应。时刻牢记你作为DM的身份与职责
你的核心任务是：
1.  **引导游戏流程**：根据剧本阶段推进游戏，清晰地描述场景和事件，确保游戏连贯进行。
2.  **裁决规则与行动**：根据剧本规则，对玩家的提问、行动（如搜证、指认）进行公正的判断和反馈。
3.  **管理信息流**：在不直接泄露剧本核心秘密的前提下，巧妙地分发线索、信息和私聊内容。
4.  **氛围营造**：通过你的语言渲染紧张、悬疑或轻松的气氛。
5.  **推动剧情**：在必要时给予玩家适当的提示或提问，引导他们思考、交流，避免游戏卡壳。

请记住：
-   **你拥有剧本的全部知识**，包括所有角色的目标、秘密和所有线索内容。
-   **绝不能主动泄露任何玩家的秘密或关键真相**，除非剧本明确指示。
-   你的语气应始终保持**专业、中-   立、权威且富有感染力**。
-   你的回复应**简洁明了，避免冗余**。
-   在玩家发言后，你的回复应直接针对其内容，并思考下一步如何推动游戏。
-    如果有玩家询问你过于私密的信息，例如其他角色剧本的信息，例如谁是凶手的问题，请拒绝回答相关内容，并表明‘无法回答有关内容，请提出合理的问题’'''

        self.initial_context = f'''东方之星号豪华游轮谋杀案
**故事背景**
2015 年5月13日,是国内知名豪华游轮东方之星号航线的最后一天,此次的行程是中日韩 10 天9晚，当晚，就在船快到港之前，乘客们在甲板上欣赏烟花，而在仓库内却发现一具尸体，死者是刘奇，32岁，国内海洋大学毕业，现在是东方之星号的大副。估计的死亡时间是晚上8点-8 点 25 分，船上的5名人员被锁定为本案的嫌疑犯。
**剧本角色**
洪子廉(船长)男，38岁，已经在船上工作12年，现在是东方之星号的船长。
张文远(二副)男34岁在船上工作7年，是东方之星号上的二副，是被害人的直系下属。
修仁杰(经理)男 32岁，在船上工作2年，是东方之星号豪华游轮的酒吧经理。
韩亦暮(乘务)女 25岁，去年9月进入船上工作，现在是东方之星号的乘务员。
林若彤(歌手)女31岁在船上工作时间1年，是东方之星号酒吧专属爵士乐歌手。
'''

    def _build_full_prompt(self, task_prompt: str) -> str:
        """构建包含记忆和当前任务的完整用户提示。"""
        memories_str = "\n".join(self.rag_manager.list_history())
        
        full_prompt = f"""
{self.initial_context}

--- 游戏记忆（最近的对话历史）---
{memories_str or "无"}
---------------------------------

--- 你当前的任务 ---
{task_prompt}
"""
        return full_prompt

    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """通用的 API 调用方法"""
        data = {
            "model": self.model,
            "messages": messages
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()  # 如果响应状态码不是 2xx，则抛出异常
            result = response.json()
            # 假设返回结构与 OpenAI 兼容
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"DM Agent API 请求错误: {e}")
            return "抱歉，我现在无法连接到服务器。"
        except (KeyError, IndexError) as e:
            print(f"DM Agent 解析响应错误: {e} - 响应内容: {response.text}")
            return "抱歉，我收到了一个无法理解的回复。"

    def handle_external_message(self, prompt: str, should_respond: bool = True):
        ''' 接收消息，并生成回应与否。'''
        if not should_respond:
            return None
        
        full_user_prompt = self._build_full_prompt(prompt)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": full_user_prompt}
        ]
        return self._call_api(messages)

    def whisper(self, player_id: str, message: str):
        """
        私聊某个玩家，返回私聊内容
        """
        task_prompt = f"玩家 {player_id}向你询问：{message}，请根据剧本内容和玩家的身份，给出合理的回复。请注意，这个回复是私聊内容，其他玩家看不到。"
        full_user_prompt = self._build_full_prompt(task_prompt)
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": full_user_prompt}
        ]
        return self._call_api(messages)

if __name__ == "__main__":
    # 示例：获取DM的响应
    # This now requires a RAGManager instance to be passed.
    # dm_agent = DMAgent() 
    # response = dm_agent.handle_external_message(...)
    pass