
import os

from openai import OpenAI

kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")
kAPI_BASE_URL_OPENROUTER: str = "https://openrouter.ai/api/v1"


class ConversationManager:
	def __init__(self, model="openai/gpt-4o-mini", max_tokens=12000):
		self.client = OpenAI(
			base_url=kAPI_BASE_URL_OPENROUTER,
			api_key=kAPI_KEY_OPENROUTER,
		)
		self.model = model
		self.max_tokens = max_tokens
		self.messages = [
			{"role": "system", "content": "你是一个专业的中文 AI 助手。"}
		]

	def add_user_message(self, content: str):
		self.messages.append({"role": "user", "content": content})

	def add_assistant_message(self, content: str):
		self.messages.append({"role": "assistant", "content": content})

	def get_reply(self, user_input: str) -> str:
		# 保存用户输入
		self.add_user_message(user_input)

		# 如果对话太长 -> 截断/总结
		if self._estimate_tokens() > self.max_tokens:
			self._summarize_history()

		# 调用 API
		response = self.client.chat.completions.create(
			model=self.model,
			messages=self.messages,
			temperature=0.7,
		)
		reply = response.choices[0].message.content

		# 保存助手回复
		self.add_assistant_message(reply)
		return reply

	def _estimate_tokens(self) -> int:
		"""简单估算 tokens 数量（粗略，用长度代替）"""
		return sum(len(m["content"]) for m in self.messages)

	def _summarize_history(self):
		"""把长历史总结成一段简短描述，减少上下文长度"""
		summary_prompt = [
			{"role": "system", "content": "请把以下对话总结成简短的上下文摘要，保留关键信息。"},
			{"role": "user", "content": "\n".join(
				f"{m['role']}: {m['content']}" for m in self.messages if m["role"] != "system"
			)}
		]

		response = self.client.chat.completions.create(
			model=self.model,
			messages=summary_prompt,
			temperature=0.3
		)
		summary = response.choices[0].message.content

		# 只保留 system + 总结
		self.messages = [
			{"role": "system", "content": "你是一个专业的中文 AI 助手。"},
			{"role": "user", "content": f"这是之前对话的摘要：{summary}"}
		]
		pass

	pass


# --- 使用示例 ---
if __name__ == "__main__":
	chat = ConversationManager()

	while True:
		user_input = input("User: ")
		if user_input.lower() in ["exit", "quit"]:
			break
		reply = chat.get_reply(user_input)
		print("Assistant:", reply)
		pass
	pass


