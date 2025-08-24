
from typing import List, Iterable, Tuple
from multiprocessing import Pool
import time
import os

from openai import AsyncOpenAI, OpenAI

from together import AsyncTogether, Together


def chat_with_openrouter(api_key: str, promote: str = None,
						model_name: str = "openai/gpt-4o-mini",
						url: str = "https://openrouter.ai/api/v1",
						message: List[str] = None,
						):
	client = OpenAI(
		base_url=url,
		api_key=api_key,
	)

	if message is None:
		message = [
			{
				"role": "user",
				"content": promote
			}
		]
		pass

	completion = client.chat.completions.create(
		model = model_name,
		messages = message,
	)
	
	return completion


async def chat_with_openrouter_on_coroutine(api_key: str, promote: str = None,
											model_name: str = "openai/gpt-4o-mini",
											url: str = "https://openrouter.ai/api/v1",
											message: List[str] = None,
											):
	async_client = AsyncOpenAI(
		api_key=api_key,
		base_url=url,
	)
	
	if message is None:
		message = [
			{
				"role": "user",
				"content": promote
			}
		]
		pass
	
	task = async_client.chat.completions.create(
		model=model_name,
		messages=message,
	)
	return await task


def chat_list_with_openrouter_on_coroutine(api_key: str, promote_list: Iterable[str], prmote_prefix: str = None,
												common_other_message: List[str] = None,
												model_name: str = "openai/gpt-4o-mini",
												url: str = "https://openrouter.ai/api/v1",
												):
	async_client = AsyncOpenAI(
		api_key=api_key,
		base_url=url,
	)

	task_list = []
	if prmote_prefix is None:
		prmote_prefix = ''
		pass
	if common_other_message is None:
		common_other_message = []
		pass
	
	for promote in promote_list:
		message = [
			{
				"role": "user", "content": prmote_prefix + promote
			},
		]

		for m in common_other_message:
			message.append(m)
			pass
		task_list.append(async_client.chat.completions.create(
			model=model_name,
			messages=message,
		))
		pass
	
	return task_list


def chat_with_together(api_key: str, promote: str = None,
						model_name: str = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
						message: List[str] = None,
						):
	client = Together(api_key=api_key)

	if message is None:
		message = [
			{
				"role": "user",
				"content": promote
			}
		]
		pass

	completion = client.chat.completions.create(
		model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
		messages=message,
	)
	
	return completion


async def chat_with_together_on_coroutine(api_key: str, promote: str = None, 
											model_name: str = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
											message: List[str] = None,
											):
	async_client = AsyncTogether(api_key=api_key)
	if message is None:
		message = [
			{
				"role": "user",
				"content": promote
			}
		]
		pass

	task = async_client.chat.completions.create(
		model=model_name,
		messages=message,
	)
	
	return await task


def chat_list_with_together_on_coroutine(api_key: str, promote_list: List[str], prmote_prefix: str = None,
												common_other_message: List[str] = None,
												model_name: str = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
												):
	async_client = AsyncTogether(
		api_key=api_key,
	)

	task_list = []
	if prmote_prefix is None:
		prmote_prefix = ''
		pass
	if common_other_message is None:
		common_other_message = []
		pass
	
	for promote in promote_list:
		message = [
			{
				"role": "user", "content": prmote_prefix + promote
			},
		]

		for m in common_other_message:
			message.append(m)
			pass
		task_list.append(async_client.chat.completions.create(
			model=model_name,
			messages=message,
		))
		pass
	
	return task_list


def _chat_with_together_on_thread(index: int, api_key: str, message: str, promote_raw: str, limit: int, model_name: str):
	if limit > 0:
		time.sleep(1)
		pass

	client = Together(api_key=api_key)

	completion = client.chat.completions.create(
		model=model_name,
		messages=message,
	)
	# print(f"Chat with Together on thread, model: {model_name}, message: {message} completion: {completion}")
	print(f"Chat with Together on thread index: {index}, completion: {completion}")
	if completion.choices:
		content = completion.choices[0].message.content.strip()
		return promote_raw, content
	return None

def chat_list_with_together_on_thread(api_key: str, promote_list: Iterable[str], prmote_prefix: str = None,
												common_other_message: List[str] = None,
												limit: int = 10, # qps limit
												model_name: str = "meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo"
												) -> List[Tuple[str, str]]:

	if prmote_prefix is None:
		prmote_prefix = ''
		pass
	if common_other_message is None:
		common_other_message = []
		pass
	
	message_list = []
	for promote in promote_list:
		message = []

		for m in common_other_message:
			message.append(m)
			pass
		message.append(
			{
				"role": "user", "content": prmote_prefix + promote
			}
		)

		message_list.append((message, promote))
		pass

	args_list = []
	index = 0
	for message, promote_raw in message_list:
		args_list.append((index, api_key, message, promote_raw, limit, model_name))
		index += 1
		pass

	process_count = None
	if limit > 0:
		process_count = max(os.cpu_count(), limit)

	with Pool(processes=process_count) as p:
		result = p.starmap(_chat_with_together_on_thread, args_list)
		return result
	return
