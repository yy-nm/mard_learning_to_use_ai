
from typing import List, Iterable, Tuple, Dict, Any, Union

import base64
import requests
import json

from openai import OpenAI


def encode_image_to_base64(image_path):
	with open(image_path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')


def chat_image_with_nano_banana_via_openrouter(api_key: str, promote: str = None,
						model_name: str = "google/gemini-2.5-flash-image-preview",
						url: str = "https://openrouter.ai/api/v1",
						image_path: str = None,
						image_url: str = None,
						image_size: str = None,
						):
	client = OpenAI(
		base_url=url,
		api_key=api_key,
	)

	prompt = promote if promote is not None else "Generate an image based on the provided content."

	content = [
		{
			"type": "text",
			"text": prompt
		}
	]

	extra_body = None
	if image_size is not None:
		extra_body = {
			"modalities": ["image", "text"],
			"image_config" : {
				# "aspect_ratio": "16:9",
				"image_size": image_size
			}
			# "provider": {'sort': 'price',} # prioritize lowest price
		}
		pass

	if image_path is not None:
		image_data = encode_image_to_base64(image_path)
		content.append(
			{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
		)
		pass
	elif image_url is not None:
		content.append(
			{"type": "image_url", "image_url": {"url": image_url}}
		)
		pass

	completion = client.chat.completions.create(
		model=model_name,
		messages=[{"role": "user", "content": content}],
		extra_body=extra_body,
	)

	result = []

	result_message = completion.choices[0].message
	# 有下发图片
	if hasattr(result_message, 'images'):
		images = result_message.images
		for image in images:
			if image['type'] == 'image_url':
				image_url = image['image_url']['url']
				data_and_file_extension = split_image_data_to_content_and_file_extension(image_url)
				result.append(data_and_file_extension)
				pass
			else:
				print("no images in response 1")
				pass
			pass
		pass
	else:
		print("no images in response 2")
		pass

	return result

def chat_image_with_nano_banana_via_openrouter_with_url(api_key: str, promote: str,
						model_name: str = "google/gemini-2.5-flash-image-preview",
						url: str = "https://openrouter.ai/api/v1/chat/completions",
						image_path: str = None,
						image_url: str = None,
						image_path_list: Iterable[str] = None,
						image_size: str = None,
						stream: bool = True,
						) -> Union[List[Tuple[bytes, str]], None]:
	
	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json"
	}
	content = [
		{"type": "text", "text": promote},
	]
	if image_path is not None:
		image_data = encode_image_to_base64(image_path)
		content.append(
			{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
		)
		pass
	elif image_url is not None:
		content.append(
			{"type": "image_url", "image_url": {"url": image_url}}
		)
		pass
	elif image_path_list is not None:
		for path in image_path_list:
			image_data = encode_image_to_base64(path)
			content.append(
				{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
			)
			pass
		pass

	messages = [
		{
			"role": "user",
			"content": content,
		}
	]

	payload: Dict[str, Any] = {
		"model": model_name,
		"messages": messages,
		# "provider": {'sort': 'price',} # prioritize lowest price
	}

	if image_size is not None:
		payload["image_config"] = {
			# 'aspect_ratio': "16:9",
			"image_size": image_size
		}
		payload['modalities'] = ['image','text']
		pass
	if stream:
		payload['stream'] = True
		pass

	response = requests.post(url, headers=headers, json=payload)

	result = []

	if response is None or not response.ok:
		print(f"request failed: {response}")
		return None

	if stream:
		for line in response.iter_lines():
			if line:
				line = line.decode('utf-8')
				if line.startswith('data: '):
					data = line[6:]
					if data != '[DONE]':
						try:
							chunk = json.loads(data)
							if chunk.get("choices"):
								delta = chunk["choices"][0].get("delta", {})
								if delta.get("reasoning"):
									print(f"Reasoning: {delta['reasoning']}")
								if delta.get("images"):
									for image in delta["images"]:
										image_info = image['image_url']['url']
										data_and_file_extension = split_image_data_to_content_and_file_extension(image_info)
										result.append(data_and_file_extension)
										pass
						except json.JSONDecodeError:
							continue
						pass
					pass
				pass
			pass
		print('stream deal done')
		pass
	else:
		raw_content = response.content.strip()
		data = json.loads(raw_content.decode('utf-8'))
		if 'choices' in data and len(data['choices']) > 0:
			result_message = data['choices'][0]['message']
			if 'images' in result_message and len(result_message['images']) > 0:
				for image in result_message['images']:
					if image['type'] == 'image_url':
						image_url = image['image_url']['url']
						data_and_file_extension = split_image_data_to_content_and_file_extension(image_url)
						result.append(data_and_file_extension)
						pass
					else:
						print("no images in response 1")
						pass
					pass
				pass
			else:
				print("no images in response 2")
				pass
			pass
		else:
			print("response empty")
			pass
		pass

	return result


def split_image_data_to_content_and_file_extension(whole_data: str) -> Tuple[bytes, str]:
	# format:  data:image/png;base64,...
	# 去掉可能的前后空白字符
	whole_data = whole_data.strip()
	header, encoded = whole_data.split(",", 1)
	# 补齐长度
	missing_padding = len(encoded) % 4
	if missing_padding:
		encoded += '=' * (4 - missing_padding)
		pass
	data = base64.b64decode(encoded)

	# file extension
	file_info, tag = header.split(";", 1)
	tag2, file_extension = file_info.split("/", 1)

	return data, file_extension
