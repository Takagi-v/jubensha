import os
import json
import requests
from typing import Dict, Any, List, Optional
from script_content import PLAYER_SCRIPTS , CHARACTERS,CLUES,INITIAL_PROMPTS
from submodule.memory_rag.memory import RAGmanager
import random


class AIPlayerAgent:
    def __init__(self, player_id: str, role_name: str, rag_manager: RAGmanager, model_name: str = "gemini-2.5-flash"):
        self.player_id = player_id
        self.role_name = role_name
        self.rag_manager = rag_manager
        self.model = model_name

        self.api_url = "https://api.xi-ai.cn/v1/chat/completions"
        # 警告：为了测试，密钥暂时硬编码。在生产环境中，请务必使用环境变量或安全的密钥管理方式。
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer "
        }

        self.name = CHARACTERS[player_id]["name"]
        self.profession = CHARACTERS[player_id]["character_name"]
        self.description = PLAYER_SCRIPTS[player_id]["character"]["description"]
        self.statement = PLAYER_SCRIPTS[player_id]["statement"]
        self.secrets = PLAYER_SCRIPTS[player_id]["secrets"]
        self.relationships = PLAYER_SCRIPTS[player_id]["relationships"]
        self.scenario = PLAYER_SCRIPTS[player_id]["case_scenario"]
        self.other_info = PLAYER_SCRIPTS[player_id]["other_info"]
        self.rules = PLAYER_SCRIPTS[player_id]["rules"]

        self.knowledge_base: Dict[str, Any] = {
            "role_info": {},
            "clues_obtained": {},
            "memories": [],
        }
        self.receive_initial_knowledge()

        print(f"AI Player Agent '{self.player_id}' 初始化成功，角色名：{self.name}，职业：{self.profession}")

    def receive_initial_knowledge(self):
        """
        接收并存储在游戏开始时分发给它的信息。
        """
        # 构建角色信息，使用传入的初始化参数
        self.knowledge_base = {
            "role_info": {
                "character": {"name": self.role_name, "description": self.description},
                "statement": self.statement,
                "secrets": self.secrets,
                "other_info": self.other_info,
                "rules": self.rules,
                "relationships": self.relationships,
            },
            "clues_obtained": [],
            "memories": [],
        }

        self.base_persona = {
            "name": self.role_name,
            "role_description": self.description,
            "secrets": self.secrets,  # 存储所有秘密
        }

        if isinstance(self.secrets, list):
            self.base_persona["secrets"] = self.secrets
        else:
            self.base_persona["secrets"] = [self.secrets]

        print(f"AI Player Agent '{self.player_id}': 接收初始角色知识。")
        
    def _call_api(self, messages: List[Dict[str, str]]) -> str:
        """通用的 API 调用方法"""
        data = {
            "model": self.model,
            "messages": messages
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, data=json.dumps(data))
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Player Agent '{self.player_id}' API 请求错误: {e}")
            return "对不起，我现在无法连接到服务器。"
        except (KeyError, IndexError) as e:
            print(f"Player Agent '{self.player_id}' 解析响应错误: {e} - 响应内容: {response.text}")
            return "对不起，我收到了一个无法理解的回复。"

    def _build_system_prompt(self) -> str:
        """
        构建包含所有角色背景和规则的系统提示。
        """
        persona_str = f"你现在是剧本杀角色【{self.base_persona.get('name', self.role_name)}】。这个游戏共有5个角色，其中有一名人类玩家。你的任务是在遵守所有的rules的同时完成你的核心目标。"
        persona_str += f"你的背景是：{self.base_persona.get('role_description', '无背景描述')}。"

        motivation_str = f"你当前的核心动机是rules中的目的。"
        if self.base_persona.get("secrets"):
            secrets_text = ", ".join(self.base_persona["secrets"]) if isinstance(self.base_persona["secrets"], list) else self.base_persona["secrets"]
            motivation_str += f"你有一些秘密：【{secrets_text}】，你希望隐藏它，或在适当的时候利用它。"

        initial_info_str = "--- 你的初始信息 ---\n"
        initial_info_str += f"角色名: {self.role_name}\n"
        initial_info_str += f"背景: {self.description}\n"
        initial_info_str += f"你的陈述: {self.statement}\n"

        if self.secrets:
            secrets_text = "\n".join([f"- {s}" for s in self.secrets]) if isinstance(self.secrets, list) else f"- {self.secrets}"
            initial_info_str += f"你的秘密:\n{secrets_text}\n"

        if self.relationships:
            initial_info_str += "人物关系:\n"
            for rel in self.relationships:
                if isinstance(rel, dict):
                    rel_info = f"- {rel.get('name', '未知')}: {rel.get('desc', '无描述')}"
                    if rel.get("clues"):
                        rel_info += f" (线索: {', '.join(rel['clues'])})"
                    initial_info_str += rel_info + "\n"
        
        # ... [其他信息和规则的构建逻辑，与原_build_personalized_prompt类似] ...

        system_prompt = f"""
        {persona_str}
        {motivation_str}
        {initial_info_str}
        **你的行为准则**
        1.  **严格角色扮演 (RP)**：你的所有言行都必须符合这个角色的性格、背景和所知信息。
        2.  **信息限制**：你只能使用你的角色剧本中、以及游戏过程中公开获得的线索和信息进行推理和发言。
        3.  **语言风格**：请使用自然、流畅的口语化表达，模拟真实玩家的对话风格。
        ---
        """
        return system_prompt

    def _build_user_prompt(self, player_input: str) -> str:
        """
        构建包含当前记忆、线索和指令的用户输入部分。
        """
        memories_str = "\n".join(self.rag_manager.list_history())
        clues_str = "\n".join(self.knowledge_base.get("clues_obtained", []))

        user_prompt = f"""
        --- 游戏当前状态 ---
        已获线索：
        {clues_str or "无"}

        游戏记忆（最近的对话历史）：
        {memories_str or "无"}
        --------------------

        DM或真人玩家对你说："{player_input}"

        请你作为【{self.base_persona.get('name', self.role_name)}】进行回应。
        """
        return user_prompt

    def receive_clue(self, clue: str):
        """
        接收线索并存储到知识库中。
        """
        self.knowledge_base["clues_obtained"].append(clue)
        print(f"AI Player Agent '{self.player_id}': 接收私有线索: {clue}")

    def state(self, phase: str) -> str:
        """
        轮到自己发言，根据记忆和线索进行推理和陈述。
        """
        prompt_instruction = ""
        if phase == "Introduction":
            prompt_instruction = "根据你的核心目标，向大家作出自我介绍。当前游戏进入第一阶段————阐述不在场证明，请根据你自己的经历，做一下自我介绍，描述一下对死者印象并进行不在场证明的陈述，以证明自己的清白。此阶段不应当过度暴露自己信息，字数尽量控制在150字以内"
        elif phase == "Discussion":
            prompt_instruction = "现在是讨论环节，请把记忆中的信息整合成一段发言。围绕你的核心目标阐述你对案件的理解，也要针对前面他人对你的怀疑和指控(若有)进行回应。"
        elif phase == "Sharing Clue":
            prompt_instruction = "现在是分享线索环节，请根据你已知的信息进行推断，说出你希望分享的线索。"
        
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt_instruction)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = self._call_api(messages)

        print(f"[{self.name}] State Response ({phase}): {response}")
        return response

    def vote(self) -> Dict[str, str]:
        """
        处理投票阶段的逻辑，生成结构化的投票结果。
        返回一个包含 'trust_id', 'suspect_id', 'statement' 的字典。
        """
        all_player_ids = {p_info['name']: p_id for p_id, p_info in CHARACTERS.items() if p_id != self.player_id and p_id != 'dm'}
        
        prompt_instruction = f"""
        现在是投票环节。请根据你已知的所有信息和你的核心目的进行推断。
        你需要选出一位你【信任】的玩家和一位你【怀疑】的玩家。
        你的回应必须是严格的 JSON 格式，如下所示：
        {{
          "trust": "你信任的玩家的姓名",
          "suspect": "你怀疑的玩家的姓名",
          "statement": "用你的角色口吻，清晰地陈述你为什么做出这样的选择，理由是什么。"
        }}

        可供选择的玩家姓名列表：{list(all_player_ids.keys())}
        请确保你选择的姓名严格来自此列表。
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt_instruction)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        raw_response = self._call_api(messages)
        print(f"[{self.name}] Raw Vote Response: {raw_response}")

        try:
            # 尝试解析 AI 返回的 JSON
            vote_data = json.loads(raw_response.strip())
            trust_name = vote_data.get("trust")
            suspect_name = vote_data.get("suspect")
            statement = vote_data.get("statement", "我根据我的判断做出了投票。")

            trust_id = all_player_ids.get(trust_name)
            suspect_id = all_player_ids.get(suspect_name)

            if not trust_id or not suspect_id or trust_id == suspect_id:
                raise ValueError("Invalid player name or trust/suspect are the same.")

            return {"trust_id": trust_id, "suspect_id": suspect_id, "statement": statement}

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"AI vote parsing for {self.name} failed: {e}. Falling back to random vote.")
            # 如果解析失败，执行随机投票作为后备方案
            other_ids = list(all_player_ids.values())
            trust_id = random.choice(other_ids)
            suspect_id = random.choice([x for x in other_ids if x != trust_id])
            
            trust_name = CHARACTERS[trust_id]['name']
            suspect_name = CHARACTERS[suspect_id]['name']
            statement = f"我仔细想了想，还是决定信任 {trust_name}，同时，我对 {suspect_name} 抱有一些怀疑。"
            
            return {"trust_id": trust_id, "suspect_id": suspect_id, "statement": statement}


    def accuse(self) -> Dict[str, str]:
        """
        处理指控阶段的逻辑，生成结构化的指控结果。
        返回一个包含 'accused_id', 'statement' 的字典。
        """
        all_player_ids = {p_info['name']: p_id for p_id, p_info in CHARACTERS.items() if p_id != self.player_id and p_id != 'dm'}

        prompt_instruction = f"""
        现在是最终指认环节。这是你最后的机会，请根据你已知的所有信息和你的核心目的，做出最终的判断。
        你需要选出一位你认为是【凶手】的玩家。
        你的回应必须是严格的 JSON 格式，如下所示：
        {{
          "accused": "你指认的凶手姓名",
          "statement": "用你的角色口吻，详细地陈述你为什么指认他/她，并提出你的最终推理或案情总结。"
        }}

        可供选择的玩家姓名列表：{list(all_player_ids.keys())}
        请确保你选择的姓名严格来自此列表。
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(prompt_instruction)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        raw_response = self._call_api(messages)
        print(f"[{self.name}] Raw Accuse Response: {raw_response}")

        try:
            accuse_data = json.loads(raw_response.strip())
            accused_name = accuse_data.get("accused")
            statement = accuse_data.get("statement", "经过深思熟虑，我指认的凶手就是你。")

            accused_id = all_player_ids.get(accused_name)

            if not accused_id:
                raise ValueError("Invalid player name provided.")

            return {"accused_id": accused_id, "statement": statement}

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"AI accuse parsing for {self.name} failed: {e}. Falling back to random accusation.")
            other_ids = list(all_player_ids.values())
            accused_id = random.choice(other_ids)
            
            accused_name = CHARACTERS[accused_id]['name']
            statement = f"所有的线索都指向了一个人……我最终决定指认的凶手是 {accused_name}。"
            
            return {"accused_id": accused_id, "statement": statement}

    
    def act_and_respond(self, signal, external_input: str) -> Optional[str]:
        """
        AI Player Agent 的主入口，处理外部输入并生成回应。
        """
        if signal == "Introduction":
            return self.state("Introduction")

        if signal == "Discussion":
            return self.state("Discussion")

        # 更新公开信息/线索
        if signal == "public_clue_receive":
            self.receive_clue(external_input)
            return None # Just receive, don't respond

        # 私聊 (假设私聊后需要回应)
        if signal == "private_conversation":
            self.receive_clue(external_input)
            return self.state("Sharing Clue")

        if signal == "Sharing Clue":
            return self.state("Sharing Clue")

        # 信任阶段
        if signal == "trust_vote" or signal == "suspect_vote":
            return self.vote()

        # 投票阶段
        if signal == "accuse":
            return self.accuse()
        
        return None



if __name__ == "__main__":
    # This requires a running RAG manager instance.
    # Example cannot be run standalone without more setup.
    pass


