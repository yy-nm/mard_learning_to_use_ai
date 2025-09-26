
from http import client
from typing import List, Iterable, Tuple
import base64
import requests

from openai import OpenAI


def encode_image_to_base64(image_path):
	with open(image_path, "rb") as image_file:
		return base64.b64encode(image_file.read()).decode('utf-8')
	pass


def chat_openai_with_web_search_via_openrouter(api_key: str, promote: str = None,
						model_name: str = "openai/gpt-4o-mini",
						url: str = "https://openrouter.ai/api/v1",
						):
	client = OpenAI(
		base_url=url,
		api_key=api_key,
	)

	response = client.responses.create(
		model=model_name,
		tools=[{"type": "web_search"}],
		input=promote,
	)

	return response


def chat_gemini_with_web_search_via_openrouter(api_key: str, promote: str, 
									model_name = "google/gemini-2.5-flash",
									# model_name = "google/gemini-2.5-pro",
									url = "https://openrouter.ai/api/v1/chat/completions",
									):

	headers = {
		"Authorization": f"Bearer {api_key}",
		"Content-Type": "application/json"
	}
	# Read and encode the audio file

	messages = [
		{
			"role": "user",
			"content": [
				# {
					# "parts": [
					# 	{
					# 		"text": promote
					# 	},
					# ],
				# },
				{
					"type": "text",
					"text": promote,
				},
			],
			"tools": [
				{
					"google_search": {}
				},
			],
		}
	]

	payload = {
		"model": model_name,
		"messages": messages,
	}

	response = requests.post(url, headers=headers, json=payload)
	return response
