import os

from openai import OpenAI


kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")
kAPI_BASE_URL_OPENROUTER: str = "https://openrouter.ai/api/v1"

kModel = 'openai/gpt-5-mini'


def main():

	client = OpenAI(
		base_url=kAPI_BASE_URL_OPENROUTER,
		api_key=kAPI_KEY_OPENROUTER,
	)

	messages = [
		# {"role": "user", "content": "小明的爸爸有三个儿子：大毛、二毛，第三个儿子是谁？"},
		# {"role": "user", "content": "已知sqrt(2)约等于1.414，要求不用数学库，求sqrt(2)精确到小数点后10位"},
		{"role": "user", "content": "从innodb的索引结构分析，为什么索引的 key 长度不能太长"},
	]

	# 调用 API
	response = client.chat.completions.create(
		model=kModel,
		messages=messages,
		temperature=0.7,
		reasoning_effort="medium"
	)
	reply_message = response.choices[0].message
	reply = reply_message.content
	if 'reasoning_details' in reply_message.model_extra:
		reasoning_details = reply_message.model_extra['reasoning_details']
		for detal in reasoning_details:
			if detal['type'] == 'reasoning.encrypted':
				continue
			print(f"🤖 AI 推理细节 ({detal['type']}):\n", detal['summary'])
			pass

	if 'reasoning' in reply_message.model_extra:
		reasoning = reply_message.model_extra['reasoning']
		print("🤖 AI 推理过程:\n", reasoning)

	print("🤖 AI:", reply)
	pass


if __name__ == "__main__":
	main()
	pass
