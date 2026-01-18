
import os
import argparse
import sys
import base64
import json

if __name__ == "__main__":
	sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
	pass

from aihelper import imagehelper

kAPI_KEY_OPENROUTER = os.getenv("API_KEY_OPENROUTER", "")

kImageGeneratePromote = '''
创建一张图， 图片为卡通风格， 图上有如下内容
一只小狐狸背书书包上学
'''
kImageSizeDefault = "1K" # 1K, 2K, 4K
kModelDefaultName = 'google/gemini-3-pro-image-preview' # nano banan pro

def _do_image_edit(promote: str, output_path: str,  model_name: str = kModelDefaultName):

	response = imagehelper.chat_image_with_nano_banana_via_openrouter(
		api_key=kAPI_KEY_OPENROUTER,
		promote=promote,
		model_name=model_name,
		image_size=kImageSizeDefault,
	)
	
	print(response)

	# 处理响应
	result_message = response.choices[0].message

	# 有下发图片
	if hasattr(result_message, 'images'):
		images = result_message.images
		image = images[0]
		if image['type'] == 'image_url':
			image_url = image['image_url']['url']
			decode_base64_image(image_url.encode('utf-8'), output_path)
			pass
		else:
			print("no images in response 1")
			pass
		pass
	else:
		print("no images in response 2")
		pass
	pass


def do_nano_banana_image_with_http(promote: str, output_path: str, model_name: str = kModelDefaultName):
	is_stream = kImageSizeDefault == '4K'
	response = imagehelper.chat_image_with_nano_banana_via_openrouter_with_url(
		api_key=kAPI_KEY_OPENROUTER,
		model_name=model_name,
		promote=promote,
		image_size=kImageSizeDefault,
		stream=is_stream, # 4k use stream
	)

	if response is None or not response.ok:
		print(f"request failed: {response}")
		return

	if is_stream:
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
									index = 0
									for image in delta["images"]:
										image_info = image['image_url']['url'].encode('utf-8')
										print(f"Generated image: {image_info[:50]}...")
										suffix = get_file_suffix(image_info)
										path = f"{output_path}.{index}.{suffix}"
										decode_base64_image(image_info, path)
										index += 1
										pass
						except json.JSONDecodeError:
							continue
			pass
		print('stream deal done')
		return
		pass

	# print(response)
	raw_content = response.content.strip()

	# result_file_path = file + ".nano_banana_result.json"
	# with open(result_file_path, "wb") as f:
	# 	f.write(raw_content)
	# 	pass
	
	# print(f"result saved to: {result_file_path}")

	data = json.loads(raw_content.decode('utf-8'))
	if 'choices' in data and len(data['choices']) > 0:
		result_message = data['choices'][0]['message']
		if 'images' in result_message and len(result_message['images']) > 0:
			image = result_message['images'][0]
			if image['type'] == 'image_url':
				image_url = image['image_url']['url']
				# print(f"image_url: {image_url}")
				decode_base64_image(image_url.encode('utf-8'), output_path)
				pass
			else:
				print("no images in response 1")
				pass
			pass
		else:
			print("no images in response 2")
			pass
		pass
	else:
		print("response empty")
		pass

	# 处理响应
	# result_message = response.choices[0].message
	# raw_content = result_message.content.strip()
	# print(f"result_message: {result_message}")

	# 有下发图片
	# if hasattr(result_message, 'images'):
	# 	images = result_message.images
	# 	image = images[0]
	# 	if image['type'] == 'image_url':
	# 		image_url = image['image_url']['url']
	# 		print(f"image_url: {image_url}")
	# 		decode_base64_image(image_url.encode('utf-8'), result_file_path + ".png")
	# 		pass
	# 	pass
	pass


def decode_base64_image(data: bytes, output_path: str):
	# 去掉可能的前后空白字符
	data = data.strip()
	# 补齐长度
	missing_padding = len(data) % 4
	if missing_padding:
		data += b'=' * (4 - missing_padding)
		pass

	header, encoded = data.split(b",", 1)
	data = base64.b64decode(encoded)
	with open(output_path, "wb") as f:
		f.write(data)
		pass
	print(f"Image saved to: {output_path}, header: {header}")
	pass

def get_file_suffix(data: bytes) -> str:
	data = data.strip()
	header, encoded = data.split(b";", 1)
	stuff, suffix = header.split(b"/", 1)

	return suffix.decode("utf-8")



def do_action(promote: str, output_path: str):
	# _do_image_edit(promote, output_path)
	do_nano_banana_image_with_http(promote, output_path)
	pass


def main():
	parser = argparse.ArgumentParser(description="generate image with nano banana pro model")
	parser.add_argument("--promote", default=kImageGeneratePromote, help="prompt for image generation")
	parser.add_argument("--output", default="./generate_image.jpg", help="Path to the output image file")

	args = parser.parse_args()
	do_action(args.promote, args.output)
	pass


if __name__ == "__main__":
	main()
	pass
