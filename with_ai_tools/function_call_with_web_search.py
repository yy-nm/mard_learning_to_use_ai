import os
import json
import requests
# import logging

from ddgs import DDGS

from openai import OpenAI


kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")
kAPI_BASE_URL_OPENROUTER: str = "https://openrouter.ai/api/v1"

kCrawHost = "http://192.168.3.109:11235"
kCrawlURL = f"{kCrawHost}/crawl"
kCrawlTask = f"{kCrawHost}/task/"

kModel = "openai/gpt-4.1-mini"


# 定义函数 schema（给 GPT 看）
# the schema only for tools calling in openrouter
tools = [
	{
		"type": "function",
		"function": {
			"name": "seach_with_duckduckgo",
			"description": "使用 DuckDuckGo 搜索引擎进行网络搜索",
			"parameters": {
				"type": "object",
				"properties": {
					"query": {
						"type": "string",
						"description": "搜索查询关键词或问题"
					}
				},
				"required": ["query"],
				"additionalProperties": False,
			},
			"strict": True,
		},
	},
	{
		"type": "function",
		"function": {
			"name": "crawl_whole_web_info",
			"description": "爬取指定 URL 的网页内容",
			"parameters": {
				"type": "object",
				"properties": {
					"url": {
						"type": "string",
						"description": "要爬取的网页 URL"
					}
				},
				"required": ["url"],
				"additionalProperties": False,
			},
			"strict": True,
		},
	}
]

def seach_with_duckduckgo(query: str) -> str:
	results = DDGS().text(query, max_results=10)
	print(f"搜索到 {len(results)} 条结果")
	for result in results:
		print(result)
		pass
	return "\n".join([result["body"] for result in results])


def crawl_whole_web_info(url: str) -> str:
	"""Crawl whole web info from a given URL"""
	response = requests.post(kCrawlURL, json={"urls": [url], "priority": 10})

	if response.status_code != 200:
		return f"Error: Unable to crawl the URL {url}. Status code: {response.status_code}"
	
	if "results" in response.json():
		results = response.json()["results"]
		print("Crawl job completed. Results:")
		return deal_with_crawl_result(results, url)
	else:
		task_id = response.json()["task_id"]
		print(f"Crawl job submitted. Task ID:: {task_id}")
		result = requests.post(f"{kCrawlTask}/{task_id}")
		if result.status_code != 200:
			return f"Error: Unable to retrieve results for task ID {task_id}. Status code: {result.status_code}"
		print(f"Results retrieved for task ID {task_id}")
		
		results = response.json()["results"]
		return deal_with_crawl_result(results, url)
	pass


def deal_with_crawl_result(results: list, original_url: str) -> str:
	output = []
	for result in results:
		data = deal_with_crawl_single_result(result, original_url)
		if data:
			output.append(data)
			pass
		pass

	return '\n'.join(output)

def deal_with_crawl_single_result(result: dict, original_url: str) -> str:
	# process the crawl result here
	url = result.get("url", "")
	print(f"url: {url}, status_code: {result['status_code']}")
	print(f"url: {url}, error_message: {result['error_message']}")

	if not result['success']:
		print(f"url: {url}, crawl not success")
		return ""

	if url != original_url:
		print(f"url: {url}, not match origin url: {original_url}")
		return ""
	
	markdown = result.get("markdown", "")
	markdown_data = json.dumps(markdown, ensure_ascii=False)
	# print(f"url: {url}, markdown data: {markdown_data}")

	print(f"url: {url}, length of html: {len(result['html'])}")
	print(f"url: {url}, length of fit_html: {len(result['fit_html'])}")
	print(f"url: {url}, length of cleaned_html: {len(result['cleaned_html'])}")
	print(f"url: {url}, length of markdown_data: {len(markdown_data)}")
	# return result['html']
	result_candidate_list = ['html', 'fit_html', 'cleaned_html']
	output_data = ''
	output_len = 0
	for candidate in result_candidate_list:
		if candidate in result and result[candidate]:
			if len(result[candidate]) < output_len or output_len == 0:
				output_data = result[candidate]
				output_len = len(result[candidate])
				pass
			pass
		pass
	if len(markdown_data) < output_len:
		output_data = markdown_data
		output_len = len(markdown_data)
		pass

	return output_data

def main():
	client = OpenAI(
		base_url=kAPI_BASE_URL_OPENROUTER,
		api_key=kAPI_KEY_OPENROUTER,
	)
	max_iterations = 10
	iteration_count = 0

	# 用户提问
	user_message = {"role": "user", "content": "搜索一下有关于 BPF 网页并对其内容进行总结"}
	message_list = [user_message]

	while iteration_count < max_iterations:
		iteration_count += 1
		print(f"--- Iteration {iteration_count} ---")
		
		# 第一步：让模型决定是否调用函数
		response = client.chat.completions.create(
			model=kModel,
			messages=message_list,
			tools=tools,
		)

		message = response.choices[0].message
		message_list.append(message.model_dump())
	
		if message.tool_calls:
			tool_data = deal_with_tools_call(message)
			if not tool_data:
				print("No tool data returned")
				return
			message_list.append(tool_data)
		else:
			print("Final response from model:")
			print(message.content)
			break
		pass
	pass


def deal_with_tools_call(message) -> dict:
	tool_call = message.tool_calls[0]
	fn_name = tool_call.function.name
	args = json.loads(tool_call.function.arguments)

	if fn_name == "get_weather":
		pass
	elif fn_name == "seach_with_duckduckgo":
		result = seach_with_duckduckgo(**args)
		return {
			"role": "tool",
			"tool_call_id": tool_call.id,
			"content": result,
		}
	elif fn_name == "crawl_whole_web_info":
		result = crawl_whole_web_info(**args)

		return {
			"role": "tool",
			"tool_call_id": tool_call.id,
			"content": result,
		}
		pass
	pass


if __name__ == "__main__":
	main()
	pass