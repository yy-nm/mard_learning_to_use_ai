
from typing import List, Iterable, Tuple
import base64
import requests

from openai import OpenAI


def encode_image_to_base64(image_path):
	with open(image_path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')
	pass


def chat_image_with_nano_banana_via_openrouter(api_key: str, promote: str = None,
						model_name: str = "google/gemini-2.5-flash-image-preview",
						url: str = "https://openrouter.ai/api/v1",
						image_path: str = None,
						image_url: str = None,
						):
	client = OpenAI(
		base_url=url,
		api_key=api_key,
	)

	if image_path is None and image_url is None:
		raise ValueError("Either image_path or image_url must be provided.")

	prompt = promote if promote is not None else "Generate an image based on the provided content."

	content = [
		{
			"type": "text",
			"text": prompt
		}
	]

	if image_path is not None:
		image_data = encode_image_to_base64(image_path)
		content.append(
			{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
		)
		pass
	else:
		content.append(
			{"type": "image_url", "image_url": {"url": image_url}}
		)
		pass

	completion = client.chat.completions.create(
		model=model_name,
		messages=[{"role": "user", "content": content}],
	)

	return completion

def chat_image_with_nano_banana_via_openrouter_with_url(api_key: str, promote: str,
						model_name: str = "google/gemini-2.5-flash-image-preview",
						url: str = "https://openrouter.ai/api/v1/chat/completions",
						image_path: str = None,
						image_url: str = None,
						):
	
	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json"
	}

	if image_path is None and image_url is None:
		raise ValueError("Either image_path or image_url must be provided.")

	content = [
		{"type": "text", "text": promote},
	]
	if image_path is not None:
		image_data = encode_image_to_base64(image_path)
		content.append(
			{"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
		)
		pass
	else:
		content.append(
			{"type": "image_url", "image_url": {"url": image_url}}
		)
		pass

	messages = [
		{
			"role": "user",
			"content": content,
		}
	]

	payload = {
		"model": model_name,
		"messages": messages,
	}

	response = requests.post(url, headers=headers, json=payload)
	return response

