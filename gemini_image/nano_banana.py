
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

# kTargetImageFile = './img6.jpg'
kTargetImageFolder = './imgs'

kImagePromote = '''
请将图片中的人物制作成手办模型放在电脑桌上， 手办本身带着底座， 手办的风格是二次元风格，
手办旁边的位置上放着手办的包装盒， 包装盒上仅仅显示手办图样，
背景的电脑上显示制作手办的3D软件界面， 界面里显示当前图片，
整体风格为二次元写实风格， 
最后请将图内容直接下发。
'''
kResultFileSuffix = ".nano_banana_result.json.png"


# kImagePromoteForOpenAI = '''
# 请将这张人物照片转换为日本动画角色风格，柔和色调，使用手绘的人物设计风格， 怀旧童话。保持原始照片中的面部表情和姿势，但用日本动画标志性的人物比例和面部特征重新绘制。
# 最后请将图内容直接下发。
# '''
# kImagePromoteForOpenAI = 'restyle the phone into studio ghibli art.'
kImagePromoteForOpenAI = '请用皮卡四风格重绘这张人物照片，保持原始照片中的面部表情和姿势。最后请将图内容直接下发。'
kResultFileSuffixForOpenAI = ".openai.json.png"
kModelNameForOpenAI = "openai/gpt-5"

def do_image_edit(image_path: str, file_suffix: str = kResultFileSuffix, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):
	file = image_path
	if os.path.isabs(file) is False:
		file = os.path.abspath(file)
		# file = os.path.join(os.path.dirname(__file__), file)
		pass
	print(f"file: {file}")

	result_image_path = file + file_suffix
	if os.path.exists(result_image_path):
		print(f"result_image_path exists, skip: {result_image_path}")
		return
	_do_image_edit(file, result_image_path, promote, model_name)
	pass

def _do_image_edit(input_path: str, output_path: str, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):

	if not os.path.exists(input_path):
		print(f"input_path not exists: {input_path}")
		return

	response = imagehelper.chat_image_with_nano_banana_via_openrouter(
		api_key=kAPI_KEY_OPENROUTER,
		promote=promote,
		model_name=model_name,
		image_path=input_path,
		# image_size="4k",
	)
	

	# print(response)

	# result_file_path = file + ".nano_banana_result.json"
	# 处理响应
	result_message = response.choices[0].message
	# raw_content = result_message.content.strip()
	# print(f"result_message: {result_message}")

	# 有下发图片
	if hasattr(result_message, 'images'):
		images = result_message.images
		image = images[0]
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


def do_nano_banana_image_with_http(image_path: str, promote: str = kImagePromote, model_name: str = "google/gemini-2.5-flash-image-preview"):
	file = image_path
	if os.path.isabs(file) is False:
		file = os.path.abspath(file)
		# file = os.path.join(os.path.dirname(__file__), file)
		pass
	print(f"file: {file}")

	result_image_path = file + kResultFileSuffix

	if os.path.exists(result_image_path):
		print(f"result_image_path exists, skip: {result_image_path}")
		return
		pass

	# promote = kImagePromote
	response = imagehelper.chat_image_with_nano_banana_via_openrouter_with_url(
		api_key=kAPI_KEY_OPENROUTER,
		model_name=model_name,
		promote=promote,
		image_path=file,
		image_size="4k",
	)

	if response is None or not response.ok:
		print(f"request failed: {response}")
		return

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
				decode_base64_image(image_url.encode('utf-8'), result_image_path)
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


# def test_decode_image():
# 	result_file_path = kTargetImageFile + ".nano_banana_result.json"
# 	output_image_path = kTargetImageFile + ".nano_banana_result.png"

# 	result_file_path = os.path.join(os.path.dirname(__file__), result_file_path)
# 	output_image_path = os.path.join(os.path.dirname(__file__), output_image_path)

# 	with open(result_file_path, 'rb') as f:
# 		data = f.read()
# 		pass
# 	print(data)
# 	decode_base64_image(data, output_image_path)
# 	pass


def test_case():
	# file = os.path.join(os.path.dirname(__file__), kTargetImageFile)
	folder = kTargetImageFolder
	if os.path.isabs(folder) is False:
		folder = os.path.join(os.path.dirname(__file__), folder)
		pass
	print(f"folder: {folder}")
	for entry in os.listdir(folder):
		file_name = entry.lower()
		if file_name.endswith(('.png', '.jpg', '.jpeg')) and not entry.endswith(kResultFileSuffix):
			file_path = os.path.join(folder, entry)
			# do_image_edit(file_path)
			# do_image_edit(file_path, model_name="google/gemini-3-pro-image-preview")
			# do_image_edit(file_path, file_suffix=kResultFileSuffixForOpenAI, promote=kImagePromoteForOpenAI, model_name=kModelNameForOpenAI)
			# do_nano_banana_image_with_http(file_path)
			do_nano_banana_image_with_http(file_path, model_name="google/gemini-3-pro-image-preview")
			pass
		pass
	# do_image_edit(file)
	# do_nano_banana_image_with_http(file)
	# test_decode_image()
	pass


def do_action(input_path: str, output_path: str):
	_do_image_edit(input_path, output_path)
	pass


def main():
	parser = argparse.ArgumentParser(description="edit image with nano banana model")
	parser.add_argument("--input", help="Path to the image file")
	parser.add_argument("--output", help="Path to the output image file")

	args = parser.parse_args()

	test_case()
	# do_action(args.input, args.output)
	pass


if __name__ == "__main__":
	main()
	pass
